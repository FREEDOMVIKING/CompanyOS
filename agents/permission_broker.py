#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

R=Path.home()/"companyos";M=R/"ceo_memory"
CFG=M/"permission_broker_config.json";REG=M/"connector_registry.json"
STATE=M/"permission_broker_state.json";HEALTH=M/"permission_broker_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def build():
    cfg=load(CFG,{})
    connectors=load(REG,{}).get("connectors",[])
    matrix=[]
    for c in connectors:
        enabled=bool(c.get("enabled"))
        can_read=enabled and bool(c.get("read")) and cfg.get("allow_automatic_read_only",True)
        write_capable=enabled and bool(c.get("write"))
        matrix.append({
          "connector_id":c.get("id"),"enabled":enabled,
          "automatic_read_allowed":can_read,
          "automatic_write_allowed":False,
          "write_capable":write_capable,
          "write_requires_owner_approval":write_capable
        })
    state={"generated_at":now(),"default_deny":True,"permissions":matrix}
    save(STATE,state)
    save(HEALTH,{"healthy":True,"last_built_at":now(),
                 "connector_count":len(matrix),
                 "automatic_read_count":sum(x["automatic_read_allowed"] for x in matrix),
                 "automatic_write_count":0})
    return {"success":True,"status":"permission_matrix_built","state":state}

def status():
    return {"success":True,"status":"permission_broker_status",
            "config":load(CFG,{}),"state":load(STATE,{}),"health":load(HEALTH,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=build() if a=="build" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["build","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
