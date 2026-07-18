#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone
from pathlib import Path

R=Path.home()/"companyos"; M=R/"ceo_memory"
CFG=M/"connector_runtime_config.json"; REG=M/"connector_registry.json"
PERM=M/"permission_broker_state.json"; STATE=M/"connector_runtime_state.json"
HEALTH=M/"connector_runtime_health.json"; AUDIT=M/"connector_runtime_audit.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp");t.write_text(json.dumps(d,indent=2));t.replace(p)
def audit(x):
    a=load(AUDIT,[]); a.append(x); save(AUDIT,a[-2000:])

def resolve(connector_id):
    reg=load(REG,{}).get("connectors",[])
    perm=load(PERM,{}).get("permissions",[])
    c=next((x for x in reg if x.get("id")==connector_id),None)
    p=next((x for x in perm if x.get("connector_id")==connector_id),None)
    if not c:return {"success":False,"status":"connector_not_registered"}
    if not c.get("enabled"):return {"success":False,"status":"connector_disabled"}
    return {"success":True,"connector":c,"permission":p or {}}

def dispatch(connector_id, operation="read"):
    resolved=resolve(connector_id)
    if not resolved.get("success"):
        audit({"timestamp":now(),"connector":connector_id,"operation":operation,"result":resolved})
        return resolved
    p=resolved["permission"]
    if operation=="read":
        allowed=bool(p.get("automatic_read_allowed"))
        result={"success":allowed,
                "status":"read_dispatch_ready" if allowed else "read_not_permitted",
                "connector":connector_id,
                "adapter_status":"interface_ready_no_live_binding"}
    else:
        result={"success":False,"status":"gateway_approval_required",
                "connector":connector_id,"operation":operation}
    audit({"timestamp":now(),"connector":connector_id,"operation":operation,"result":result})
    return result

def build():
    reg=load(REG,{}).get("connectors",[])
    adapters=[]
    for c in reg:
        r=resolve(c.get("id"))
        adapters.append({
          "connector_id":c.get("id"),
          "enabled":bool(c.get("enabled")),
          "runtime_ready":bool(r.get("success")),
          "read_ready":bool(r.get("permission",{}).get("automatic_read_allowed")) if r.get("success") else False,
          "write_route":"execution_gateway"
        })
    state={"generated_at":now(),"adapters":adapters}
    save(STATE,state)
    save(HEALTH,{"healthy":True,"last_built_at":now(),"adapter_count":len(adapters),
                 "runtime_ready_count":sum(x["runtime_ready"] for x in adapters)})
    return {"success":True,"status":"connector_runtime_built","state":state}

def status():
    return {"success":True,"status":"connector_runtime_status",
            "config":load(CFG,{}),"state":load(STATE,{}),"health":load(HEALTH,{})}

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="build":r=build()
elif a=="status":r=status()
elif a=="dispatch" and len(sys.argv)>=3:r=dispatch(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else "read")
else:r={"success":False,"status":"unknown_action","allowed":["build","status","dispatch <connector> <read|write>"]}
print(json.dumps(r,indent=2));raise SystemExit(0 if r.get("success") else 1)
