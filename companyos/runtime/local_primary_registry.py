from __future__ import annotations
import argparse, json, os, platform, shutil, socket, time
from pathlib import Path
from typing import Any

RT=Path.home()/".companyos_runtime"
STATE=RT/"local_primary_host.json"
NODE_META=Path.home()/".companyos_remote_node"

def atomic(path:Path,obj:Any):
    path.parent.mkdir(parents=True,exist_ok=True)
    t=path.with_suffix(path.suffix+".tmp")
    t.write_text(json.dumps(obj,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    t.replace(path)
    try:path.chmod(0o600)
    except Exception:pass

def load(path:Path,default:Any):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return default

def node_metadata():
    out={}
    if not NODE_META.exists():return out
    for raw in NODE_META.read_text(encoding="utf-8",errors="replace").splitlines():
        line=raw.strip()
        if line and not line.startswith("#") and "=" in line:
            k,v=line.split("=",1); out[k.strip()]=v.strip()
    return out

def private_ipv4():
    for target in (("1.1.1.1",53),("8.8.8.8",53)):
        s=None
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            s.settimeout(1); s.connect(target)
            ip=s.getsockname()[0]
            if ip and not ip.startswith("127."):return ip
        except Exception:pass
        finally:
            try:
                if s:s.close()
            except Exception:pass
    return None

def memory_gib():
    try:
        for raw in Path("/proc/meminfo").read_text().splitlines():
            if raw.startswith("MemTotal:"):
                return round(float(raw.split()[1])/1024/1024,2)
    except Exception:pass
    return 0.0

def disk_free_gib():
    try:return round(shutil.disk_usage(Path.home()).free/(1024**3),2)
    except Exception:return 0.0

def capacity_score(cores,ram_gib,free_gib):
    return round(
        max(1,int(cores))*2.0
        + max(0.0,float(ram_gib))*0.75
        + min(max(0.0,float(free_gib)),500.0)*0.03,
        3,
    )

def profile():
    meta=node_metadata()
    cores=int(os.cpu_count() or 1)
    ram=memory_gib(); free=disk_free_gib()
    return {
        "schema":"companyos.local_primary_host.v69_35h",
        "updated_at_unix":time.time(),
        "node_name":meta.get("COMPANYOS_NODE_NAME") or os.getenv("COMPANYOS_NODE_NAME") or socket.gethostname(),
        "role":meta.get("COMPANYOS_NODE_ROLE") or os.getenv("COMPANYOS_NODE_ROLE") or "primary",
        "hostname":socket.gethostname(),
        "local_ip":private_ipv4(),
        "platform":platform.system().lower(),
        "platform_release":platform.release(),
        "machine":platform.machine(),
        "wsl_distro":os.getenv("WSL_DISTRO_NAME"),
        "cpu_cores":cores,
        "memory_gib":ram,
        "disk_free_gib":free,
        "capacity_score":capacity_score(cores,ram,free),
        "migrated_from":meta.get("COMPANYOS_MIGRATED_FROM"),
        "handoff_at":meta.get("COMPANYOS_HANDOFF_AT"),
    }

def register():
    previous=load(STATE,{})
    cur=profile()
    cur["registered_at_unix"]=previous.get("registered_at_unix") or time.time()
    cur["refresh_count"]=int(previous.get("refresh_count") or 0)+1
    atomic(STATE,cur)
    return cur

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("register","status"))
    a=p.parse_args()
    out=register() if a.command=="register" else load(STATE,{"status":"not_registered"})
    print(json.dumps(out,indent=2,sort_keys=True,default=str))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
