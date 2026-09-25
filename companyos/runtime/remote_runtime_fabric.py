from __future__ import annotations
import argparse, base64, json, os, shlex, shutil, subprocess, tarfile, tempfile, time
from pathlib import Path
from typing import Any

ROOT=Path.home()/"companyos"
RT=Path.home()/".companyos_runtime"
INVENTORY=RT/"remote_runtime_hosts.json"
STATE=RT/"remote_runtime_fabric_state.json"
BOOTSTRAP=ROOT/"scripts/companyos_remote_bootstrap.sh"
DEFAULT_REPO=os.getenv("COMPANYOS_GIT_REPOSITORY","https://github.com/FREEDOMVIKING/CompanyOS.git")
DEFAULT_BRANCH=os.getenv("COMPANYOS_GIT_BRANCH","companyos-continuous-fix-2026-09-11")
ALLOWED_ROLES={"primary","research_worker","standby"}
WORKER_ROLES={"primary","research_worker"}
STATE_FILES=(
    "evidence_acquisition_queue.json",
    "validation_experiment_queue.json",
    "candidate_portfolio_validation_state.json",
    "evidence_coverage_rescoring_state.json",
    "live_market_intelligence_state.json",
    "provider_discovered_metadata.json",
    "authorized_local_migration_state.json",
    "local_primary_host.json",
)

def load(path:Path,default:Any):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def atomic(path:Path,obj:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(path.suffix+".tmp")
    t.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    t.replace(path)
    try:path.chmod(0o600)
    except Exception:pass

def inventory():
    d=load(INVENTORY,{"schema":"companyos.remote_runtime_hosts.v1","nodes":[]})
    if not isinstance(d,dict):d={"schema":"companyos.remote_runtime_hosts.v1","nodes":[]}
    if not isinstance(d.get("nodes"),list):d["nodes"]=[]
    return d

def safe_node(n):
    return {
        "name":n.get("name"),"provider":n.get("provider"),"role":n.get("role"),
        "ssh_target":n.get("ssh_target"),"ssh_port":n.get("ssh_port"),
        "capacity_score":n.get("capacity_score"),"enabled":bool(n.get("enabled",True)),
        "branch":n.get("branch"),"repo":n.get("repo"),
    }

def sanitized_inventory():
    d=inventory()
    return {"schema":d.get("schema"),"nodes":[safe_node(x) for x in d["nodes"] if isinstance(x,dict)],"secret_values_emitted":False}

def add_node(name,provider,role,ssh_target,ssh_port=22,identity_file=None,capacity_score=1.0,repo=DEFAULT_REPO,branch=DEFAULT_BRANCH):
    name=str(name).strip(); target=str(ssh_target).strip(); role=str(role).strip().lower()
    if not name:raise ValueError("node_name_required")
    if role not in ALLOWED_ROLES:raise ValueError("invalid_role")
    if not target or any(x in target for x in (" ","\n","\r")):raise ValueError("invalid_ssh_target")
    port=int(ssh_port)
    if not 1<=port<=65535:raise ValueError("invalid_ssh_port")
    d=inventory()
    nodes=[x for x in d["nodes"] if not isinstance(x,dict) or str(x.get("name") or "")!=name]
    node={
        "name":name,"provider":str(provider or "generic").lower(),"role":role,
        "ssh_target":target,"ssh_port":port,
        "identity_file":str(Path(identity_file).expanduser()) if identity_file else None,
        "capacity_score":max(0.1,float(capacity_score)),
        "repo":str(repo or DEFAULT_REPO),"branch":str(branch or DEFAULT_BRANCH),
        "enabled":True,"authorized_by_user":True,"created_at_unix":time.time(),
    }
    nodes.append(node); d["nodes"]=nodes; d["updated_at_unix"]=time.time(); atomic(INVENTORY,d)
    return safe_node(node)

def remove_node(name):
    d=inventory(); old=d["nodes"]
    new=[x for x in old if not isinstance(x,dict) or str(x.get("name") or "")!=str(name)]
    d["nodes"]=new; d["updated_at_unix"]=time.time(); atomic(INVENTORY,d)
    return len(new)!=len(old)

def node_by_name(name):
    for n in inventory()["nodes"]:
        if isinstance(n,dict) and str(n.get("name") or "")==name:return n
    raise KeyError("node_not_found:"+name)

def ssh_cmd(n):
    c=["ssh","-o","BatchMode=yes","-o","ConnectTimeout=10","-o","ServerAliveInterval=10","-o","ServerAliveCountMax=2","-o","StrictHostKeyChecking=accept-new","-p",str(int(n.get("ssh_port") or 22))]
    if n.get("identity_file"):c+=["-i",str(n["identity_file"])]
    c.append(str(n["ssh_target"]))
    return c

def scp_cmd(n):
    c=["scp","-q","-o","BatchMode=yes","-o","ConnectTimeout=10","-o","StrictHostKeyChecking=accept-new","-P",str(int(n.get("ssh_port") or 22))]
    if n.get("identity_file"):c+=["-i",str(n["identity_file"])]
    return c

def run(cmd,timeout=60):
    return subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,check=False)

def probe_node(n):
    started=time.time()
    if not n.get("enabled",True):return {"name":n.get("name"),"healthy":False,"reason":"disabled"}
    p=run(ssh_cmd(n)+["printf 'SSH_OK '; python3 -c 'import sys; print(sys.version_info.major)'"],timeout=20)
    return {
        "name":n.get("name"),"provider":n.get("provider"),"role":n.get("role"),
        "healthy":p.returncode==0 and "SSH_OK" in p.stdout,
        "latency_seconds":round(time.time()-started,3),"returncode":p.returncode,
        "stderr_preview":p.stderr[-300:] if p.returncode else "",
    }

def probe_all():
    rows=[]
    for n in inventory()["nodes"]:
        if not isinstance(n,dict):continue
        try:rows.append(probe_node(n))
        except Exception as e:rows.append({"name":n.get("name"),"healthy":False,"error":f"{type(e).__name__}:{str(e)[:300]}"})
    out={"schema":"companyos.remote_runtime_fabric_state.v69_35a","updated_at_unix":time.time(),"node_count":len(rows),"healthy_node_count":sum(1 for x in rows if x.get("healthy")),"nodes":rows,"secret_values_emitted":False}
    atomic(STATE,out); return out

def bootstrap_node(name):
    n=node_by_name(name)
    if not BOOTSTRAP.exists():raise RuntimeError("bootstrap_script_missing")
    if shutil.which("ssh") is None or shutil.which("scp") is None:raise RuntimeError("openssh_required")
    remote="~/.companyos_remote_bootstrap.sh"
    p=run(scp_cmd(n)+[str(BOOTSTRAP),f"{n['ssh_target']}:{remote}"],timeout=60)
    if p.returncode:raise RuntimeError("bootstrap_copy_failed:"+p.stderr[-500:])
    args=["bash",remote,str(n.get("role") or "research_worker"),str(n.get("repo") or DEFAULT_REPO),str(n.get("branch") or DEFAULT_BRANCH)]
    p=run(ssh_cmd(n)+[" ".join(shlex.quote(x) for x in args)],timeout=300)
    if p.returncode:raise RuntimeError("bootstrap_remote_failed:"+p.stderr[-800:])
    return {"name":name,"healthy":True,"role":n.get("role"),"stdout_preview":p.stdout[-600:]}

def bootstrap_all():
    out=[]
    for n in inventory()["nodes"]:
        if not isinstance(n,dict) or not n.get("enabled",True):continue
        try:out.append(bootstrap_node(str(n["name"])))
        except Exception as e:out.append({"name":n.get("name"),"healthy":False,"error":f"{type(e).__name__}:{str(e)[:600]}"})
    return {"results":out,"successful":sum(1 for x in out if x.get("healthy")),"failed":sum(1 for x in out if not x.get("healthy"))}

def worker_nodes():
    rows=[x for x in inventory()["nodes"] if isinstance(x,dict) and x.get("enabled",True) and str(x.get("role") or "") in WORKER_ROLES]
    rows.sort(key=lambda x:(-float(x.get("capacity_score") or 1.0),str(x.get("name") or "")))
    return rows

def ordered_nodes(rows):
    if not rows:return []
    st=load(STATE,{})
    cur=int(st.get("dispatch_cursor") or 0)%len(rows)
    out=rows[cur:]+rows[:cur]
    st["dispatch_cursor"]=(cur+1)%len(rows); st["updated_at_unix"]=time.time(); atomic(STATE,st)
    return out

def search_web_remote(query,max_results=8):
    if os.getenv("COMPANYOS_REMOTE_WORKER_LOCAL_ONLY","0")=="1":raise RuntimeError("remote_dispatch_disabled_on_worker")
    rows=ordered_nodes(worker_nodes())
    if not rows:raise RuntimeError("no_remote_workers_enrolled")
    encoded=base64.urlsafe_b64encode(str(query).encode()).decode()
    attempts=[]
    for n in rows:
        remote=("cd ~/companyos && export COMPANYOS_REMOTE_WORKER_LOCAL_ONLY=1 && "
                "PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python; "
                "$PY -m companyos.runtime.remote_research_worker search --query-b64 "
                +shlex.quote(encoded)+" --max-results "+str(max(1,min(12,int(max_results)))))
        started=time.time()
        try:
            p=run(ssh_cmd(n)+[remote],timeout=55)
            if p.returncode:
                attempts.append({"node":n.get("name"),"status":"failed","error":p.stderr[-250:]}); continue
            lines=[x.strip() for x in p.stdout.splitlines() if x.strip()]
            if not lines:
                attempts.append({"node":n.get("name"),"status":"failed","error":"empty_response"}); continue
            data=json.loads(lines[-1])
            data["provider"]="remote_runtime_fabric:"+str(n.get("name"))
            data["remote_node"]=n.get("name")
            data["remote_provider"]=n.get("provider")
            data["fabric_latency_seconds"]=round(time.time()-started,3)
            data["attempts"]=attempts+[{"node":n.get("name"),"status":"success"}]
            return data
        except Exception as e:
            attempts.append({"node":n.get("name"),"status":"failed","error":f"{type(e).__name__}:{str(e)[:250]}"})
    raise RuntimeError("remote_workers_failed:"+json.dumps(attempts)[:1000])

def state_members():
    out=[]
    for name in STATE_FILES:
        p=RT/name
        if p.exists() and p.is_file():out.append(p)
    d=RT/"profit_first_candidates"
    if d.exists():out.extend(p for p in d.glob("*.json") if p.is_file())
    return out

def sync_state(name):
    n=node_by_name(name); members=state_members()
    with tempfile.TemporaryDirectory(prefix="companyos-state-") as d:
        archive=Path(d)/"state.tar.gz"
        with tarfile.open(archive,"w:gz") as tf:
            for p in members:tf.add(p,arcname=str(p.relative_to(RT)),recursive=False)
        p=run(ssh_cmd(n)+["mkdir -p ~/.companyos_runtime ~/.companyos_runtime/profit_first_candidates"],timeout=30)
        if p.returncode:raise RuntimeError("remote_state_dir_failed")
        p=run(scp_cmd(n)+[str(archive),f"{n['ssh_target']}:~/.companyos_runtime/companyos_state_import.tar.gz"],timeout=120)
        if p.returncode:raise RuntimeError("state_copy_failed:"+p.stderr[-400:])
        p=run(ssh_cmd(n)+["cd ~/.companyos_runtime && tar -xzf companyos_state_import.tar.gz && rm -f companyos_state_import.tar.gz"],timeout=60)
        if p.returncode:raise RuntimeError("state_extract_failed:"+p.stderr[-400:])
    return {"name":name,"healthy":True,"state_files_synced":len(members),"secret_files_synced":0}

def remote_health(name):
    n=node_by_name(name)
    p=run(ssh_cmd(n)+["cd ~/companyos && PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python; $PY scripts/companyosctl health"],timeout=35)
    try:data=json.loads(p.stdout)
    except Exception:data={}
    return {"name":name,"returncode":p.returncode,"healthy":bool(data.get("healthy")),"health":data,"stderr_preview":p.stderr[-300:]}

def start_remote(name):
    n=node_by_name(name)
    p=run(ssh_cmd(n)+["cd ~/companyos && PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python; $PY scripts/companyosctl start"],timeout=45)
    return {"name":name,"started":p.returncode==0,"returncode":p.returncode,"stdout_preview":p.stdout[-700:],"stderr_preview":p.stderr[-300:]}

def handoff_primary(name):
    n=node_by_name(name)
    if n.get("role")!="primary":raise RuntimeError("target_role_must_be_primary")
    b=bootstrap_node(name); s=sync_state(name); start=start_remote(name)
    deadline=time.time()+60; h=None
    while time.time()<deadline:
        h=remote_health(name)
        if h.get("healthy"):break
        time.sleep(2)
    if not h or not h.get("healthy"):
        return {"healthy":False,"handoff_completed":False,"local_runtime_stopped":False,"bootstrap":b,"state_sync":s,"start":start,"remote_health":h}
    local=run(["python","scripts/companyosctl","stop"],timeout=40)
    return {"healthy":local.returncode==0,"handoff_completed":local.returncode==0,"local_runtime_stopped":local.returncode==0,"remote_health":h}

def monitor(interval=60):
    interval=max(30,int(interval))
    while True:
        try:probe_all()
        except Exception as e:atomic(STATE,{"healthy":False,"updated_at_unix":time.time(),"error":f"{type(e).__name__}:{str(e)[:500]}"})
        time.sleep(interval)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("inventory"); sub.add_parser("probe"); sub.add_parser("bootstrap-all")
    a=sub.add_parser("add-node")
    a.add_argument("--name",required=True); a.add_argument("--provider",required=True); a.add_argument("--role",required=True,choices=sorted(ALLOWED_ROLES))
    a.add_argument("--ssh-target",required=True); a.add_argument("--ssh-port",type=int,default=22); a.add_argument("--identity-file")
    a.add_argument("--capacity-score",type=float,default=1.0); a.add_argument("--repo",default=DEFAULT_REPO); a.add_argument("--branch",default=DEFAULT_BRANCH)
    r=sub.add_parser("remove-node"); r.add_argument("--name",required=True)
    b=sub.add_parser("bootstrap"); b.add_argument("--name",required=True)
    s=sub.add_parser("sync-state"); s.add_argument("--name",required=True)
    h=sub.add_parser("remote-health"); h.add_argument("--name",required=True)
    hp=sub.add_parser("handoff-primary"); hp.add_argument("--name",required=True)
    m=sub.add_parser("monitor"); m.add_argument("--interval",type=int,default=60)
    x=p.parse_args()
    if x.command=="inventory":print(json.dumps(sanitized_inventory(),indent=2,sort_keys=True))
    elif x.command=="probe":print(json.dumps(probe_all(),indent=2,sort_keys=True))
    elif x.command=="bootstrap-all":print(json.dumps(bootstrap_all(),indent=2,sort_keys=True))
    elif x.command=="add-node":print(json.dumps(add_node(x.name,x.provider,x.role,x.ssh_target,x.ssh_port,x.identity_file,x.capacity_score,x.repo,x.branch),indent=2,sort_keys=True))
    elif x.command=="remove-node":print(json.dumps({"removed":remove_node(x.name)}))
    elif x.command=="bootstrap":print(json.dumps(bootstrap_node(x.name),indent=2,sort_keys=True))
    elif x.command=="sync-state":print(json.dumps(sync_state(x.name),indent=2,sort_keys=True))
    elif x.command=="remote-health":print(json.dumps(remote_health(x.name),indent=2,sort_keys=True))
    elif x.command=="handoff-primary":print(json.dumps(handoff_primary(x.name),indent=2,sort_keys=True))
    else:monitor(x.interval)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
