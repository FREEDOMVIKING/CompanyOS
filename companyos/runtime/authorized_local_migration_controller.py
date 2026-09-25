from __future__ import annotations
import argparse, json, os, shlex, socket, time
from pathlib import Path
from typing import Any
from companyos.runtime import local_primary_registry as registry
from companyos.runtime import remote_runtime_fabric as fabric

RT=Path.home()/".companyos_runtime"
STATE=RT/"authorized_local_migration_state.json"
INTERVAL=max(120,int(os.getenv("COMPANYOS_LOCAL_MIGRATION_CHECK_SECONDS","600")))
MIN_GAIN=max(1.05,float(os.getenv("COMPANYOS_LOCAL_MIGRATION_MIN_GAIN","1.25")))
COOLDOWN=max(3600,int(os.getenv("COMPANYOS_LOCAL_MIGRATION_COOLDOWN_SECONDS","86400")))
AUTO=os.getenv("COMPANYOS_ENABLE_AUTHORIZED_LOCAL_AUTOMIGRATION","1")=="1"

def atomic(path:Path,obj:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(path.suffix+".tmp")
    t.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    t.replace(path)
    try:path.chmod(0o600)
    except Exception:pass

def load_state():
    try:
        d=json.loads(STATE.read_text(encoding="utf-8"))
        return d if isinstance(d,dict) else {}
    except Exception:return {}

def eligible_nodes():
    rows=[]
    for n in fabric.inventory().get("nodes") or []:
        if not isinstance(n,dict):continue
        if not n.get("enabled",True):continue
        if not n.get("authorized_by_user"):continue
        if not str(n.get("ssh_target") or ""):continue
        rows.append(n)
    return rows

def remote_capacity(n):
    probe=fabric.probe_node(n)
    if not probe.get("healthy"):
        return {"name":n.get("name"),"healthy":False,"reason":"ssh_probe_failed","probe":probe}

    code=r'''
import json,os,shutil,socket
from pathlib import Path
ram=0.0
try:
    for raw in Path("/proc/meminfo").read_text().splitlines():
        if raw.startswith("MemTotal:"):
            ram=round(float(raw.split()[1])/1024/1024,2); break
except Exception:pass
try:free=round(shutil.disk_usage(Path.home()).free/(1024**3),2)
except Exception:free=0.0
cores=int(os.cpu_count() or 1)
score=round(cores*2.0+ram*0.75+min(free,500.0)*0.03,3)
print(json.dumps({"hostname":socket.gethostname(),"cpu_cores":cores,"memory_gib":ram,"disk_free_gib":free,"capacity_score":score}))
'''
    p=fabric.run(fabric.ssh_cmd(n)+["python3 -c "+shlex.quote(code)],timeout=30)
    if p.returncode:
        return {"name":n.get("name"),"healthy":False,"reason":"capacity_probe_failed","stderr_preview":p.stderr[-300:]}
    try:
        data=json.loads([x.strip() for x in p.stdout.splitlines() if x.strip()][-1])
    except Exception:
        return {"name":n.get("name"),"healthy":False,"reason":"capacity_json_invalid"}
    return {
        "name":n.get("name"),
        "healthy":True,
        "provider":n.get("provider"),
        "role":n.get("role"),
        "ssh_target":n.get("ssh_target"),
        "authorized_by_user":True,
        **data,
    }

def set_role(name,role):
    d=fabric.inventory(); changed=False
    for n in d.get("nodes") or []:
        if isinstance(n,dict) and str(n.get("name") or "")==name:
            n["role"]=role; n["updated_at_unix"]=time.time(); changed=True
    if not changed:raise KeyError("node_not_found:"+name)
    d["updated_at_unix"]=time.time()
    fabric.atomic(fabric.INVENTORY,d)

def remote_primary_metadata(n,predecessor):
    payload="\n".join([
        "COMPANYOS_NODE_ROLE=primary",
        "COMPANYOS_NODE_NAME="+str(n.get("name") or "remote-primary"),
        "COMPANYOS_MIGRATED_FROM="+str(predecessor.get("node_name") or socket.gethostname()),
        "COMPANYOS_HANDOFF_AT="+time.strftime("%Y%m%d_%H%M%S"),
    ])+"\n"
    cmd="cat > ~/.companyos_remote_node <<'EOF'\n"+payload+"EOF\nchmod 600 ~/.companyos_remote_node"
    p=fabric.run(fabric.ssh_cmd(n)+[cmd],timeout=20)
    if p.returncode:raise RuntimeError("remote_primary_metadata_failed:"+p.stderr[-300:])

def evaluate():
    current=registry.register()
    current_score=float(current.get("capacity_score") or 0.0)
    prior=load_state()
    candidates=[]
    for n in eligible_nodes():
        try:candidates.append(remote_capacity(n))
        except Exception as e:
            candidates.append({"name":n.get("name"),"healthy":False,"error":f"{type(e).__name__}:{str(e)[:350]}"})

    viable=[
        x for x in candidates
        if x.get("healthy")
        and str(x.get("ssh_target") or "")!=str(current.get("local_ip") or "")
    ]
    viable.sort(key=lambda x:(-float(x.get("capacity_score") or 0),str(x.get("name") or "")))
    best=viable[0] if viable else None
    required=round(current_score*MIN_GAIN,3)
    qualifies=bool(best and float(best.get("capacity_score") or 0)>=required)
    last=float(prior.get("last_successful_handoff_at_unix") or 0.0)
    cooldown_ok=(time.time()-last)>=COOLDOWN

    out={
        "schema":"companyos.authorized_local_migration.v69_35h",
        "updated_at_unix":time.time(),
        "healthy":True,
        "automatic_migration_enabled":AUTO,
        "current_primary":current,
        "minimum_gain_ratio":MIN_GAIN,
        "required_candidate_score":required,
        "authorized_candidate_count":len(candidates),
        "candidates":candidates,
        "best_candidate":best,
        "best_candidate_qualifies":qualifies,
        "cooldown_ok":cooldown_ok,
        "action":"none",
        "handoff":None,
        "last_successful_handoff_at_unix":last or None,
        "policy":{
            "requires_authorized_by_user":True,
            "password_guessing":True,
            "credential_harvesting":True,
            "exploit_attempts":True,
            "firewall_bypass":True,
        },
    }

    if not (AUTO and qualifies and cooldown_ok and best):
        atomic(STATE,out)
        return out

    name=str(best["name"])
    node=fabric.node_by_name(name)
    previous_role=str(node.get("role") or "research_worker")
    out["action"]="handoff_attempt"
    out["handoff_target"]=name
    atomic(STATE,out)

    try:
        set_role(name,"primary")
        node=fabric.node_by_name(name)

        boot=fabric.bootstrap_node(name)
        sync=fabric.sync_state(name)
        remote_primary_metadata(node,current)
        start=fabric.start_remote(name)

        deadline=time.time()+75
        health=None
        while time.time()<deadline:
            health=fabric.remote_health(name)
            if health.get("healthy"):break
            time.sleep(3)

        if not health or not health.get("healthy"):
            set_role(name,previous_role)
            out["action"]="handoff_rejected_remote_unhealthy"
            out["handoff"]={
                "bootstrap":boot,
                "state_sync":sync,
                "start":start,
                "remote_health":health,
                "local_runtime_stopped":False,
            }
            atomic(STATE,out)
            return out

        out["action"]="handoff_remote_verified_local_stop_requested"
        out["last_successful_handoff_at_unix"]=time.time()
        out["handoff"]={
            "bootstrap":boot,
            "state_sync":sync,
            "start":start,
            "remote_health":health,
            "local_runtime_stopped":"requested_after_remote_health_pass",
        }
        atomic(STATE,out)

        local_python=Path.home()/"companyos/.venv/bin/python"
        fabric.run([str(local_python),"scripts/companyosctl","stop"],timeout=45)
        return out
    except Exception as e:
        try:set_role(name,previous_role)
        except Exception:pass
        out["action"]="handoff_failed_local_remains_primary"
        out["handoff"]={"error":f"{type(e).__name__}:{str(e)[:800]}","local_runtime_stopped":False}
        atomic(STATE,out)
        return out

def loop():
    while True:
        try:evaluate()
        except Exception as e:
            atomic(STATE,{
                "schema":"companyos.authorized_local_migration.v69_35h",
                "updated_at_unix":time.time(),
                "healthy":False,
                "error":f"{type(e).__name__}:{str(e)[:800]}",
            })
        time.sleep(INTERVAL)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("evaluate","status","loop"))
    a=p.parse_args()
    if a.command=="evaluate":out=evaluate()
    elif a.command=="status":out=load_state() or {"status":"not_run"}
    else:loop(); return 0
    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
