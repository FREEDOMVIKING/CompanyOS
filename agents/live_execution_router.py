#!/usr/bin/env python3
import json,os,sys,subprocess
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"; LOG=ROOT/"logs"/"live_execution_audit.jsonl"
REG=MEM/"connector_registry.json"; AUTH=MEM/"authority_execution_config.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def audit(x):
    LOG.parent.mkdir(parents=True,exist_ok=True)
    with LOG.open("a") as f:f.write(json.dumps(x)+"\n")

def connectors(kind):
    return [c for c in load(REG,{"connectors":[]}).get("connectors",[]) if c.get("kind")==kind and c.get("enabled") and c.get("configured")]

def route(kind,payload):
    cs=connectors(kind)
    if not cs:
        r={"success":False,"status":"no_configured_connector","kind":kind,"payload":payload,"executed":False}
        audit({"at":now(),**r});return r
    c=cs[0]
    key=os.getenv(c.get("credential_env") or "","")
    if not key:
        r={"success":False,"status":"credential_unavailable","connector_id":c.get("connector_id"),"executed":False}
        audit({"at":now(),**r});return r
    # Connector execution is adapter-driven. This core never improvises a protocol.
    adapter=ROOT/"connectors"/f"{kind}_adapter.py"
    if not adapter.exists():
        r={"success":False,"status":"adapter_missing","connector_id":c.get("connector_id"),"executed":False}
        audit({"at":now(),**r});return r
    p=subprocess.run([sys.executable,str(adapter),json.dumps({"connector":c,"payload":payload})],
                     cwd=ROOT,text=True,capture_output=True,timeout=300)
    r={"success":p.returncode==0,"status":"connector_execution_complete" if p.returncode==0 else "connector_execution_failed",
       "connector_id":c.get("connector_id"),"stdout":p.stdout[-3000:],"stderr":p.stderr[-1000:],"executed":p.returncode==0}
    audit({"at":now(),"kind":kind,"payload":payload,**r});return r

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="execute":
    kind=sys.argv[2]; payload=json.loads(sys.argv[3]); r=route(kind,payload)
else:
    r={"success":True,"status":"live_execution_router_ready","registered_connectors":load(REG,{"connectors":[]})}
print(json.dumps(r,indent=2))
