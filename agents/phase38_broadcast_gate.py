#!/usr/bin/env python3
import json,sys
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
CFG=MEM/"phase38_broadcast_activation_config.json"
STATE=MEM/"phase38_route_state.json"
P37=MEM/"phase37_safety_config.json"
P34=MEM/"phase34_autonomous_treasury_config.json"

def now(): return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

def route(cfg,chain,asset):
    return (((cfg.get("canary_limits") or {}).get(chain) or {}).get(asset))

def sync_global(enable):
    p37=load(P37,{})
    p37["broadcast_enabled"]=bool(enable)
    save(P37,p37)

def main():
    cfg=load(CFG,{})
    state=load(STATE,{"routes":{},"confirmed_canaries":[]})
    a=sys.argv[1] if len(sys.argv)>1 else "status"

    if a=="arm-canary":
        chain,asset=sys.argv[2],sys.argv[3]
        r=route(cfg,chain,asset)
        if not r:
            out={"success":False,"status":"unknown_route"}
        else:
            r["enabled"]=True
            cfg["global_broadcast_enabled"]=True
            cfg["last_armed_at"]=now()
            state.setdefault("routes",{})[f"{chain}:{asset}"]={
                "mode":"canary",
                "armed":True,
                "armed_at":now()
            }
            save(CFG,cfg);save(STATE,state);sync_global(True)
            out={"success":True,"status":"canary_armed","chain":chain,"asset":asset,"limits":r}

    elif a=="disarm":
        chain,asset=sys.argv[2],sys.argv[3]
        r=route(cfg,chain,asset)
        if r:r["enabled"]=False
        state.setdefault("routes",{})[f"{chain}:{asset}"]={
            "mode":"disabled","armed":False,"updated_at":now()
        }
        any_enabled=any(
            x.get("enabled")
            for c in cfg.get("canary_limits",{}).values()
            for x in c.values()
        )
        cfg["global_broadcast_enabled"]=bool(any_enabled)
        save(CFG,cfg);save(STATE,state);sync_global(any_enabled)
        out={"success":True,"status":"route_disarmed","chain":chain,"asset":asset}

    elif a=="emergency-off":
        for c in cfg.get("canary_limits",{}).values():
            for x in c.values(): x["enabled"]=False
        cfg["global_broadcast_enabled"]=False
        cfg["emergency_off_at"]=now()
        save(CFG,cfg);sync_global(False)
        out={"success":True,"status":"all_broadcast_routes_disabled"}

    else:
        out={
          "success":True,
          "status":"phase38_broadcast_activation_status",
          "global_broadcast_enabled":cfg.get("global_broadcast_enabled",False),
          "canary_limits":cfg.get("canary_limits",{}),
          "state":state
        }

    print(json.dumps(out,indent=2))
    return 0 if out.get("success") else 1

raise SystemExit(main())
