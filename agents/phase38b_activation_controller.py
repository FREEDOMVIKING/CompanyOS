#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase38b_activation_config.json"
STATE=MEM/"phase38b_activation_state.json"
P38=MEM/"phase38_broadcast_activation_config.json"
P38STATE=MEM/"phase38_route_state.json"
P37=MEM/"phase37_safety_config.json"
P34=MEM/"phase34_autonomous_treasury_config.json"
P35=MEM/"phase35_ceo_treasury_bridge_config.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

def route_bucket(chain,asset):
    if chain=="solana" and asset=="SOL":
        return ("solana","SOL")
    if chain=="solana" and asset in ("USDT-SPL","USDC-SPL"):
        return ("solana_tokens",asset)
    if chain=="evm":
        return ("evm",asset)
    if chain=="bitcoin":
        return ("bitcoin",asset)
    return (None,None)

def mark_canary(chain,asset,txid=None):
    s=load(STATE,{"confirmed_canaries":[],"promoted_routes":[]})
    key=f"{chain}:{asset}"
    if key not in [x.get("route") for x in s.get("confirmed_canaries",[])]:
        s.setdefault("confirmed_canaries",[]).append({
            "route":key,
            "confirmed_at":now(),
            "txid":txid
        })
    s["last_updated_at"]=now()
    save(STATE,s)
    return s

def promote(chain,asset):
    cfg=load(CFG,{})
    state=load(STATE,{"confirmed_canaries":[],"promoted_routes":[]})
    b,a=route_bucket(chain,asset)
    if not b or not ((cfg.get("production_routes") or {}).get(b) or {}).get(a):
        return {"success":False,"status":"unknown_route"}

    confirmed={x.get("route") for x in state.get("confirmed_canaries",[])}
    key=f"{chain}:{asset}"

    if cfg.get("require_confirmed_canary") and key not in confirmed:
        return {"success":False,"status":"confirmed_canary_required","route":key}

    # Enable route at production layer.
    cfg["production_routes"][b][a]["enabled"]=True
    cfg["production_routes"][b][a]["promoted_at"]=now()
    save(CFG,cfg)

    # Enable matching live route in Phase 34.
    p34=load(P34,{})
    routes=p34.setdefault("supported_live_routes",{})
    routes.setdefault(chain,[])
    if asset not in routes[chain]:
        routes[chain].append(asset)
    save(P34,p34)

    # Ensure Phase 35 bridge also recognizes route.
    p35=load(P35,{})
    routes35=p35.setdefault("supported_live_routes",{})
    routes35.setdefault(chain,[])
    if asset not in routes35[chain]:
        routes35[chain].append(asset)
    save(P35,p35)

    # Phase 37 broadcast stays governed by Phase 38 route arming.
    p37=load(P37,{})
    p37["broadcast_enabled"]=True
    save(P37,p37)

    if key not in state.get("promoted_routes",[]):
        state.setdefault("promoted_routes",[]).append(key)
    state["last_updated_at"]=now()
    save(STATE,state)

    return {
        "success":True,
        "status":"route_promoted_to_controlled_production",
        "route":key,
        "single_transaction_auto_limit_usd":cfg["single_transaction_auto_limit_usd"],
        "daily_total_limit_usd":cfg["daily_total_limit_usd"]
    }

def demote(chain,asset):
    cfg=load(CFG,{})
    state=load(STATE,{"confirmed_canaries":[],"promoted_routes":[]})
    b,a=route_bucket(chain,asset)
    if not b or not ((cfg.get("production_routes") or {}).get(b) or {}).get(a):
        return {"success":False,"status":"unknown_route"}

    cfg["production_routes"][b][a]["enabled"]=False
    cfg["production_routes"][b][a]["demoted_at"]=now()
    save(CFG,cfg)

    key=f"{chain}:{asset}"
    state["promoted_routes"]=[x for x in state.get("promoted_routes",[]) if x!=key]
    state["last_updated_at"]=now()
    save(STATE,state)

    return {"success":True,"status":"route_demoted","route":key}

def status():
    return {
        "success":True,
        "status":"phase38b_activation_status",
        "config":load(CFG,{}),
        "state":load(STATE,{}),
        "phase38":load(P38,{}),
        "phase38_state":load(P38STATE,{})
    }

a=sys.argv[1] if len(sys.argv)>1 else "status"

if a=="confirm-canary":
    chain,asset=sys.argv[2],sys.argv[3]
    txid=sys.argv[4] if len(sys.argv)>4 else None
    s=mark_canary(chain,asset,txid)
    r={"success":True,"status":"canary_recorded","route":f"{chain}:{asset}","state":s}
elif a=="promote":
    r=promote(sys.argv[2],sys.argv[3])
elif a=="demote":
    r=demote(sys.argv[2],sys.argv[3])
else:
    r=status()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
