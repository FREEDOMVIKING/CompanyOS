#!/usr/bin/env python3
import json,sys
from pathlib import Path

ROOT=Path.home()/"companyos";MEM=ROOT/"ceo_memory"
CFG=MEM/"phase38_broadcast_activation_config.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def main():
    if len(sys.argv)<6:
        print(json.dumps({"success":False,"status":"usage","usage":"CHAIN ASSET AMOUNT_NATIVE AMOUNT_USD DESTINATION"},indent=2))
        return 1

    chain,asset=sys.argv[1],sys.argv[2]
    amount_native=float(sys.argv[3]);amount_usd=float(sys.argv[4])
    cfg=load(CFG,{})
    r=(((cfg.get("canary_limits") or {}).get(chain) or {}).get(asset))

    reasons=[]
    if not cfg.get("global_broadcast_enabled"): reasons.append("global_broadcast_disabled")
    if not r: reasons.append("unknown_route")
    else:
        if not r.get("enabled"): reasons.append("route_not_armed")
        if amount_native>float(r["max_amount_native"]): reasons.append("native_canary_limit_exceeded")
        if amount_usd>float(r["max_amount_usd"]): reasons.append("usd_canary_limit_exceeded")

    out={
      "success":not reasons,
      "status":"phase38_canary_guard_passed" if not reasons else "phase38_canary_guard_blocked",
      "chain":chain,"asset":asset,
      "amount_native":amount_native,"amount_usd":amount_usd,
      "reasons":reasons
    }
    print(json.dumps(out,indent=2))
    return 0 if out["success"] else 1

raise SystemExit(main())
