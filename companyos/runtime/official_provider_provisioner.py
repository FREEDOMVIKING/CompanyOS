from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

RT=Path.home()/".companyos_runtime"
STATE=RT/"official_provider_provisioner_state.json"
HISTORY=RT/"official_provider_provisioner_history.jsonl"
SSH_PRIVATE=Path.home()/".ssh/companyos_cloud_primary"
SSH_PUBLIC=Path(str(SSH_PRIVATE)+".pub")

INTERVAL=max(300,int(os.getenv("COMPANYOS_PROVIDER_PROVISIONER_INTERVAL_SECONDS","900")))
AUTO_PROVISION=os.getenv("COMPANYOS_PROVIDER_AUTO_PROVISION","0")=="1"
AUTO_ADOPT=os.getenv("COMPANYOS_PROVIDER_AUTO_ADOPT_EXISTING","0")=="1"
HANDOFF_AFTER_PROVISION=os.getenv("COMPANYOS_PROVIDER_HANDOFF_AFTER_PROVISION","1")=="1"
MAX_MONTHLY_USD=max(0.0,float(os.getenv(
    "COMPANYOS_PROVIDER_MAX_MONTHLY_USD",
    os.getenv("COMPANYOS_HOST_SCOUT_MAX_MONTHLY_USD","7.00"),
)))
NODE_NAME=os.getenv("COMPANYOS_PROVIDER_PRIMARY_NODE_NAME","companyos-primary").strip() or "companyos-primary"


def load_env()->dict[str,str]:
    vals=dict(os.environ)
    for path in (
        Path.home()/"companyos/.env",
        Path.home()/".companyos_runtime/.env",
        Path.home()/".config/companyos/.env",
    ):
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line=raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k,v=line.split("=",1)
                k=k.strip()
                v=v.strip().strip("'").strip('"')
                if k and v and k not in vals:
                    vals[k]=v
        except Exception:
            pass
    return vals


def token_for(provider:str)->str|None:
    vals=load_env()
    if provider=="hetzner":
        return vals.get("HETZNER_API_TOKEN") or vals.get("HCLOUD_TOKEN")
    if provider=="digitalocean":
        return (
            vals.get("DIGITALOCEAN_ACCESS_TOKEN")
            or vals.get("DIGITALOCEAN_TOKEN")
            or vals.get("DO_API_TOKEN")
            or vals.get("DO_API_KEY")
        )
    return None


def atomic(path:Path,obj:Any)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    tmp.replace(path)
    try:path.chmod(0o600)
    except Exception:pass


def append_history(obj:dict[str,Any])->None:
    HISTORY.parent.mkdir(parents=True,exist_ok=True)
    with HISTORY.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,sort_keys=True,default=str)+"\n")
    try:
        lines=HISTORY.read_text(encoding="utf-8").splitlines()
        if len(lines)>400:
            HISTORY.write_text("\n".join(lines[-400:])+"\n",encoding="utf-8")
    except Exception:
        pass


def api_json(provider:str,method:str,path:str,*,body:dict[str,Any]|None=None,timeout:int=30)->tuple[int,dict[str,Any]]:
    token=token_for(provider)
    if not token:
        raise RuntimeError(f"{provider}_credential_missing")
    if provider=="hetzner":
        base="https://api.hetzner.cloud"
    elif provider=="digitalocean":
        base="https://api.digitalocean.com"
    else:
        raise ValueError("unsupported_provider")

    data=None if body is None else json.dumps(body,separators=(",",":")).encode()
    req=urllib.request.Request(
        base+path,
        data=data,
        method=method.upper(),
        headers={
            "Authorization":"Bearer "+token,
            "Accept":"application/json",
            "Content-Type":"application/json",
            "User-Agent":"CompanyOS-OfficialProviderProvisioner/69.37",
        },
    )
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read(2_000_000)
            payload=json.loads(raw.decode("utf-8","replace")) if raw else {}
            return int(r.status),payload if isinstance(payload,dict) else {"result":payload}
    except urllib.error.HTTPError as exc:
        raw=exc.read(200_000)
        try:
            payload=json.loads(raw.decode("utf-8","replace")) if raw else {}
        except Exception:
            payload={"error_preview":raw.decode("utf-8","replace")[:1000]}
        raise RuntimeError(f"{provider}_http_{exc.code}:{json.dumps(payload,default=str)[:1000]}") from None


def ensure_local_ssh_key()->dict[str,Any]:
    SSH_PRIVATE.parent.mkdir(parents=True,exist_ok=True)
    try:SSH_PRIVATE.parent.chmod(0o700)
    except Exception:pass
    if SSH_PRIVATE.exists() and SSH_PUBLIC.exists():
        return {"present":True,"created":False,"private_path":str(SSH_PRIVATE),"public_path":str(SSH_PUBLIC)}

    keygen=shutil.which("ssh-keygen")
    if not keygen:
        raise RuntimeError("ssh_keygen_not_installed")
    p=subprocess.run(
        [keygen,"-t","ed25519","-N","","-C","companyos-cloud-primary","-f",str(SSH_PRIVATE)],
        text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=30,
    )
    if p.returncode:
        raise RuntimeError("ssh_key_generation_failed:"+p.stderr[-500:])
    try:SSH_PRIVATE.chmod(0o600)
    except Exception:pass
    try:SSH_PUBLIC.chmod(0o644)
    except Exception:pass
    return {"present":True,"created":True,"private_path":str(SSH_PRIVATE),"public_path":str(SSH_PUBLIC)}


def public_key_text()->str:
    ensure_local_ssh_key()
    value=SSH_PUBLIC.read_text(encoding="utf-8").strip()
    if not value.startswith(("ssh-ed25519 ","ssh-rsa ","ecdsa-")):
        raise RuntimeError("unsupported_public_key_format")
    return value


def hetzner_readiness()->dict[str,Any]:
    if not token_for("hetzner"):
        return {"provider":"hetzner","credential_present":False,"ready":False,"reason":"credential_missing"}

    _,servers=api_json("hetzner","GET","/v1/servers?per_page=50")
    _,types=api_json("hetzner","GET","/v1/server_types?per_page=50")
    candidates=[]
    for st in types.get("server_types") or []:
        if not isinstance(st,dict) or str(st.get("architecture") or "x86")!="x86":
            continue
        memory=int(float(st.get("memory") or 0)*1024)
        for price in st.get("prices") or []:
            if not isinstance(price,dict):continue
            try:monthly=float((price.get("price_monthly") or {}).get("gross"))
            except Exception:continue
            if monthly<=0 or monthly>MAX_MONTHLY_USD:continue
            candidates.append({
                "server_type":st.get("name"),
                "location":str(price.get("location") or ""),
                "monthly_usd":monthly,
                "memory_mb":memory,
                "cores":int(st.get("cores") or 0),
                "disk_gb":int(st.get("disk") or 0),
            })
    candidates.sort(key=lambda x:(-x["memory_mb"],-x["cores"],x["monthly_usd"],str(x["server_type"])))

    existing=[]
    for s in servers.get("servers") or []:
        if not isinstance(s,dict):continue
        ipv4=(((s.get("public_net") or {}).get("ipv4") or {}).get("ip"))
        existing.append({
            "id":s.get("id"),"name":s.get("name"),"status":s.get("status"),
            "ipv4":ipv4,"server_type":(s.get("server_type") or {}).get("name"),
        })
    return {
        "provider":"hetzner","credential_present":True,"ready":bool(candidates),
        "candidate":candidates[0] if candidates else None,
        "candidate_count":len(candidates),"existing_servers":existing,
        "existing_companyos_primary":next((x for x in existing if x.get("name")==NODE_NAME and x.get("ipv4")),None),
        "secret_values_emitted":False,
    }


def digitalocean_readiness()->dict[str,Any]:
    if not token_for("digitalocean"):
        return {"provider":"digitalocean","credential_present":False,"ready":False,"reason":"credential_missing"}

    api_json("digitalocean","GET","/v2/account")
    _,sizes=api_json("digitalocean","GET","/v2/sizes?per_page=200")
    _,droplets=api_json("digitalocean","GET","/v2/droplets?per_page=100")

    preferred_regions=("nyc1","nyc3","fra1","sfo3","ams3","tor1","lon1","sgp1")
    candidates=[]
    for row in sizes.get("sizes") or []:
        if not isinstance(row,dict) or not row.get("available"):continue
        try:monthly=float(row.get("price_monthly") or 0)
        except Exception:continue
        if monthly<=0 or monthly>MAX_MONTHLY_USD:continue
        regions=[str(x) for x in row.get("regions") or []]
        if not regions:continue
        region=next((x for x in preferred_regions if x in regions),regions[0])
        candidates.append({
            "size":row.get("slug"),"region":region,"monthly_usd":monthly,
            "memory_mb":int(row.get("memory") or 0),"vcpus":int(row.get("vcpus") or 0),
            "disk_gb":int(row.get("disk") or 0),
        })
    candidates.sort(key=lambda x:(-x["memory_mb"],-x["vcpus"],x["monthly_usd"],str(x["size"])))

    existing=[]
    for d in droplets.get("droplets") or []:
        if not isinstance(d,dict):continue
        ipv4=None
        for net in ((d.get("networks") or {}).get("v4") or []):
            if isinstance(net,dict) and net.get("type")=="public" and net.get("ip_address"):
                ipv4=net.get("ip_address"); break
        existing.append({
            "id":d.get("id"),"name":d.get("name"),"status":d.get("status"),"ipv4":ipv4,
            "size":(d.get("size") or {}).get("slug") or d.get("size_slug"),
            "region":(d.get("region") or {}).get("slug"),
        })
    return {
        "provider":"digitalocean","credential_present":True,"ready":bool(candidates),
        "candidate":candidates[0] if candidates else None,
        "candidate_count":len(candidates),"existing_servers":existing,
        "existing_companyos_primary":next((x for x in existing if x.get("name")==NODE_NAME and x.get("ipv4")),None),
        "secret_values_emitted":False,
    }


def readiness()->dict[str,Any]:
    rows=[]
    for provider,fn in (("hetzner",hetzner_readiness),("digitalocean",digitalocean_readiness)):
        try:
            rows.append(fn())
        except Exception as exc:
            rows.append({
                "provider":provider,"credential_present":bool(token_for(provider)),
                "ready":False,"reason":"api_probe_failed",
                "error":f"{type(exc).__name__}:{str(exc)[:800]}","secret_values_emitted":False,
            })
    ready=[x for x in rows if x.get("ready")]
    ready.sort(key=lambda x:(
        -int((x.get("candidate") or {}).get("memory_mb") or 0),
        float((x.get("candidate") or {}).get("monthly_usd") or 999),
        str(x.get("provider")),
    ))
    return {
        "schema":"companyos.official_provider_readiness.v69_37",
        "updated_at_unix":time.time(),"providers":rows,
        "best_ready_provider":ready[0].get("provider") if ready else None,
        "credential_ready_count":sum(1 for x in rows if x.get("credential_present")),
        "provisioning_enabled":AUTO_PROVISION,"adopt_existing_enabled":AUTO_ADOPT,
        "max_monthly_usd":MAX_MONTHLY_USD,"secret_values_emitted":False,
    }


def hetzner_ensure_key()->dict[str,Any]:
    pub=public_key_text()
    _,data=api_json("hetzner","GET","/v1/ssh_keys?per_page=100")
    for key in data.get("ssh_keys") or []:
        if isinstance(key,dict) and (key.get("name")=="companyos-termux" or str(key.get("public_key") or "").strip()==pub):
            return {"id":key.get("id"),"created":False}
    _,created=api_json("hetzner","POST","/v1/ssh_keys",body={"name":"companyos-termux","public_key":pub})
    key=created.get("ssh_key") or {}
    if not key.get("id"):raise RuntimeError("hetzner_ssh_key_create_missing_id")
    return {"id":key["id"],"created":True}


def digitalocean_ensure_key()->dict[str,Any]:
    pub=public_key_text()
    _,data=api_json("digitalocean","GET","/v2/account/keys?per_page=200")
    for key in data.get("ssh_keys") or []:
        if isinstance(key,dict) and (key.get("name")=="companyos-termux" or str(key.get("public_key") or "").strip()==pub):
            return {"id":key.get("id"),"fingerprint":key.get("fingerprint"),"created":False}
    _,created=api_json("digitalocean","POST","/v2/account/keys",body={"name":"companyos-termux","public_key":pub})
    key=created.get("ssh_key") or {}
    if not key.get("id"):raise RuntimeError("digitalocean_ssh_key_create_missing_id")
    return {"id":key["id"],"fingerprint":key.get("fingerprint"),"created":True}


def register_primary(provider:str,ipv4:str,memory_mb:int|None=None)->dict[str,Any]:
    from companyos.runtime import remote_runtime_fabric as fabric
    score=max(1.0,float(memory_mb or 512)/512.0)
    return fabric.add_node(NODE_NAME,provider,"primary","root@"+str(ipv4),22,str(SSH_PRIVATE),score)


def maybe_handoff()->dict[str,Any]:
    if not HANDOFF_AFTER_PROVISION:
        return {"attempted":False,"reason":"handoff_disabled"}
    from companyos.runtime import remote_runtime_fabric as fabric
    return fabric.handoff_primary(NODE_NAME)


def wait_hetzner(server_id:int,timeout:int=300)->dict[str,Any]:
    deadline=time.time()+timeout
    last={}
    while time.time()<deadline:
        _,data=api_json("hetzner","GET",f"/v1/servers/{int(server_id)}")
        server=data.get("server") or {}
        last=server
        ip=(((server.get("public_net") or {}).get("ipv4") or {}).get("ip"))
        if ip and server.get("status")=="running":
            return {"server":server,"ipv4":ip}
        time.sleep(5)
    raise RuntimeError("hetzner_server_ready_timeout:"+json.dumps({"id":server_id,"status":last.get("status")})[:300])


def wait_digitalocean(droplet_id:int,timeout:int=300)->dict[str,Any]:
    deadline=time.time()+timeout
    last={}
    while time.time()<deadline:
        _,data=api_json("digitalocean","GET",f"/v2/droplets/{int(droplet_id)}")
        d=data.get("droplet") or {}
        last=d
        ip=None
        for net in ((d.get("networks") or {}).get("v4") or []):
            if isinstance(net,dict) and net.get("type")=="public" and net.get("ip_address"):
                ip=net.get("ip_address"); break
        if ip and d.get("status")=="active":
            return {"droplet":d,"ipv4":ip}
        time.sleep(5)
    raise RuntimeError("digitalocean_droplet_ready_timeout:"+json.dumps({"id":droplet_id,"status":last.get("status")})[:300])


def provision_hetzner(plan:dict[str,Any])->dict[str,Any]:
    candidate=plan.get("candidate") or {}
    monthly=float(candidate.get("monthly_usd") or 0)
    if monthly<=0 or monthly>MAX_MONTHLY_USD:
        raise RuntimeError("hetzner_candidate_outside_monthly_cap")
    key=hetzner_ensure_key()
    _,created=api_json("hetzner","POST","/v1/servers",body={
        "name":NODE_NAME,"server_type":candidate["server_type"],"image":"ubuntu-24.04",
        "location":candidate["location"],"ssh_keys":[key["id"]],"start_after_create":True,
        "labels":{"companyos":"primary","managed_by":"companyos"},
    })
    server=created.get("server") or {}
    if not server.get("id"):raise RuntimeError("hetzner_server_create_missing_id")
    ready=wait_hetzner(int(server["id"]))
    ip=str(ready["ipv4"])
    node=register_primary("hetzner",ip,int(candidate.get("memory_mb") or 0))
    return {"provider":"hetzner","resource_id":server["id"],"ipv4":ip,"monthly_usd":monthly,"node":node,"ssh_key_created":bool(key.get("created"))}


def provision_digitalocean(plan:dict[str,Any])->dict[str,Any]:
    candidate=plan.get("candidate") or {}
    monthly=float(candidate.get("monthly_usd") or 0)
    if monthly<=0 or monthly>MAX_MONTHLY_USD:
        raise RuntimeError("digitalocean_candidate_outside_monthly_cap")
    key=digitalocean_ensure_key()
    _,created=api_json("digitalocean","POST","/v2/droplets",body={
        "name":NODE_NAME,"region":candidate["region"],"size":candidate["size"],
        "image":"ubuntu-24-04-x64","ssh_keys":[key["id"]],
        "ipv6":True,"backups":False,"monitoring":False,
    })
    droplet=created.get("droplet") or {}
    if not droplet.get("id"):raise RuntimeError("digitalocean_droplet_create_missing_id")
    ready=wait_digitalocean(int(droplet["id"]))
    ip=str(ready["ipv4"])
    node=register_primary("digitalocean",ip,int(candidate.get("memory_mb") or 0))
    return {"provider":"digitalocean","resource_id":droplet["id"],"ipv4":ip,"monthly_usd":monthly,"node":node,"ssh_key_created":bool(key.get("created"))}


def adopt_existing(plan:dict[str,Any])->dict[str,Any]|None:
    existing=plan.get("existing_companyos_primary")
    if not isinstance(existing,dict) or not existing.get("ipv4"):
        return None
    provider=str(plan.get("provider"))
    candidate=plan.get("candidate") or {}
    node=register_primary(provider,str(existing["ipv4"]),int(candidate.get("memory_mb") or 512))
    return {"provider":provider,"adopted":True,"resource_id":existing.get("id"),"ipv4":existing.get("ipv4"),"node":node}


def choose_provider(snapshot:dict[str,Any])->dict[str,Any]|None:
    rows=[x for x in snapshot.get("providers") or [] if isinstance(x,dict) and x.get("ready")]
    if not rows:return None
    rows.sort(key=lambda x:(
        -int((x.get("candidate") or {}).get("memory_mb") or 0),
        float((x.get("candidate") or {}).get("monthly_usd") or 999),
        str(x.get("provider")),
    ))
    return rows[0]


def once()->dict[str,Any]:
    started=time.time()
    ssh=ensure_local_ssh_key()
    snap=readiness()
    chosen=choose_provider(snap)
    action={"performed":False,"reason":"no_credential_ready_provider"}
    handoff={"attempted":False,"reason":"no_new_primary"}

    if chosen is not None:
        if AUTO_ADOPT and chosen.get("existing_companyos_primary"):
            adopted=adopt_existing(chosen)
            action={"performed":True,"type":"adopt_existing","result":adopted}
            handoff=maybe_handoff()
        elif AUTO_PROVISION:
            provider=str(chosen["provider"])
            monthly=float((chosen.get("candidate") or {}).get("monthly_usd") or 0)
            if monthly>MAX_MONTHLY_USD:
                action={"performed":False,"reason":"monthly_cap"}
            elif provider=="hetzner":
                result=provision_hetzner(chosen)
                action={"performed":True,"type":"provision","result":result}
                handoff=maybe_handoff()
            elif provider=="digitalocean":
                result=provision_digitalocean(chosen)
                action={"performed":True,"type":"provision","result":result}
                handoff=maybe_handoff()
        else:
            action={
                "performed":False,"reason":"provisioning_disabled",
                "credential_ready_provider":chosen.get("provider"),
                "candidate":chosen.get("candidate"),
            }

    out={
        "schema":"companyos.official_provider_provisioner.v69_37",
        "updated_at_unix":time.time(),"scan_seconds":round(time.time()-started,3),
        "healthy":True,"ssh_key_present":bool(ssh.get("present")),"ssh_key_created":bool(ssh.get("created")),
        "readiness":snap,"action":action,"handoff":handoff,
        "max_monthly_usd":MAX_MONTHLY_USD,"auto_provision_enabled":AUTO_PROVISION,
        "auto_adopt_enabled":AUTO_ADOPT,
        "financial_action_performed":bool(action.get("performed") and action.get("type")=="provision"),
        "account_creation_performed":False,"credential_harvesting_performed":False,
        "secret_values_emitted":False,
    }
    atomic(STATE,out)
    append_history({
        "ts":out["updated_at_unix"],"healthy":True,
        "credential_ready_count":snap.get("credential_ready_count"),
        "best_ready_provider":snap.get("best_ready_provider"),
        "action_performed":bool(action.get("performed")),"action_type":action.get("type"),
        "handoff_attempted":bool(handoff.get("attempted")),
    })
    return out


def status()->dict[str,Any]:
    try:return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:return {"status":"not_run","state_path":str(STATE)}


def loop()->None:
    while True:
        try:once()
        except Exception as exc:
            atomic(STATE,{
                "schema":"companyos.official_provider_provisioner.v69_37",
                "updated_at_unix":time.time(),"healthy":False,
                "error":f"{type(exc).__name__}:{str(exc)[:1200]}","secret_values_emitted":False,
            })
        time.sleep(INTERVAL)


def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("once","status","readiness","loop"))
    a=p.parse_args()
    if a.command=="once":out=once()
    elif a.command=="status":out=status()
    elif a.command=="readiness":out=readiness()
    else:
        loop(); return 0
    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
