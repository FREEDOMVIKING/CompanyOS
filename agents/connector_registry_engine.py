#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
REG=MEM/"connector_registry.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load():
    try:return json.loads(REG.read_text())
    except:return {"connectors":[]}
def save(d): REG.write_text(json.dumps(d,indent=2))
def cid(kind,name): return hashlib.sha256(f"{kind}|{name}".encode()).hexdigest()[:18]

a=sys.argv[1] if len(sys.argv)>1 else "list"
d=load()

if a=="register":
    kind,name=sys.argv[2],sys.argv[3]
    c={
      "connector_id":cid(kind,name),
      "kind":kind,
      "name":name,
      "enabled":False,
      "configured":False,
      "credential_env":None,
      "target":None,
      "created_at":now()
    }
    d["connectors"]=[x for x in d.get("connectors",[]) if x.get("connector_id")!=c["connector_id"]]+[c]
    save(d); r={"success":True,"status":"connector_registered","connector":c}
elif a=="configure":
    connector_id,credential_env,target=sys.argv[2],sys.argv[3],sys.argv[4]
    found=None
    for c in d.get("connectors",[]):
        if c.get("connector_id")==connector_id:
            c["credential_env"]=credential_env;c["target"]=target;c["configured"]=True;c["updated_at"]=now();found=c
    save(d);r={"success":bool(found),"status":"connector_configured","connector":found}
elif a=="enable":
    connector_id=sys.argv[2];found=None
    for c in d.get("connectors",[]):
        if c.get("connector_id")==connector_id:
            c["enabled"]=bool(c.get("configured"));c["updated_at"]=now();found=c
    save(d);r={"success":bool(found and found.get("enabled")),"status":"connector_enable_result","connector":found}
else:
    r={"success":True,"status":"connector_registry","registry":d}
print(json.dumps(r,indent=2))
