#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"; MEM=ROOT/"ceo_memory"
CFG=MEM/"phase35_ceo_treasury_bridge_config.json"
REQ=MEM/"ceo_treasury_requests.json"

def now(): return datetime.now(timezone.utc).isoformat()
def load(p,d):
    try:return json.loads(p.read_text())
    except:return d
def save(p,d):
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(d,indent=2)); t.replace(p)
def rid(seed): return hashlib.sha256(seed.encode()).hexdigest()[:22]

def create(amount_usd, amount_native, asset, chain, destination, reason, source_decision_id):
    cfg=load(CFG,{})
    routes=cfg.get("supported_live_routes",{})
    route_supported=asset in routes.get(chain,[])
    row={
      "request_id":rid(f"{now()}|{chain}|{asset}|{destination}|{amount_native}|{source_decision_id}"),
      "created_at":now(),
      "source":"ceo",
      "source_decision_id":source_decision_id,
      "chain":chain,
      "asset":asset,
      "destination":destination,
      "amount_native":amount_native,
      "amount_usd":amount_usd,
      "reason":reason,
      "route_supported":route_supported,
      "status":"pending_bridge" if route_supported else "blocked_unsupported_route"
    }
    d=load(REQ,{"requests":[]}); d["requests"].append(row); d["updated_at"]=now(); save(REQ,d)
    return row

a=sys.argv[1] if len(sys.argv)>1 else "status"
if a=="create":
    if len(sys.argv)<9:
        r={"success":False,"status":"missing_arguments"}
    else:
        row=create(float(sys.argv[2]),float(sys.argv[3]),sys.argv[4],sys.argv[5],sys.argv[6],sys.argv[7],sys.argv[8])
        r={"success":True,"status":"ceo_treasury_request_created","request":row}
else:
    r={"success":True,"status":"ceo_treasury_request_status","queue":load(REQ,{"requests":[]})}
print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
