#!/usr/bin/env python3
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"connector_binding_config.json"; REG=M/"connector_registry.json"
PERM=M/"permission_broker_state.json"; STATE=M/"connector_binding_state.json"
HEALTH=M/"connector_binding_health.json"

def now():return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)

def bind():
    cfg=load(CFG,{})
    reg={x.get("id"):x for x in load(REG,{}).get("connectors",[])}
    perms={x.get("connector_id"):x for x in load(PERM,{}).get("permissions",[])}
    rows=[]
    for cid,spec in cfg.get("bindings",{}).items():
        connector=reg.get(cid,{})
        required=spec.get("required_env",[])
        present=[name for name in required if bool(os.getenv(name))]
        missing=[name for name in required if not os.getenv(name)]
        enabled=bool(connector.get("enabled"))
        read_allowed=bool(perms.get(cid,{}).get("automatic_read_allowed"))
        rows.append({
          "connector_id":cid,
          "registered":bool(connector),
          "enabled":enabled,
          "read_allowed":read_allowed,
          "required_environment_variables":required,
          "environment_variables_present":present,
          "environment_variables_missing":missing,
          "secret_values_recorded":False,
          "binding_ready":enabled and read_allowed and not missing,
          "write_route":"execution_gateway"
        })
    state={"generated_at":now(),"bindings":rows}
    save(STATE,state)
    save(HEALTH,{
      "healthy":True,"last_checked_at":now(),"binding_count":len(rows),
      "ready_count":sum(x["binding_ready"] for x in rows),
      "secret_values_recorded":False
    })
    return {"success":True,"status":"connector_binding_check_complete","state":state}

def status():
    return {"success":True,"status":"connector_binding_status",
            "state":load(STATE,{}),"health":load(HEALTH,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
r=bind() if a=="bind" else status() if a=="status" else {
 "success":False,"status":"unknown_action","allowed":["bind","status"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
