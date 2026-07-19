#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
CFG=MEM/"phase38a_sol_canary_config.json"
DESTS=MEM/"treasury_destination_registry.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def run(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=300)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json","stdout":p.stdout[-3000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def registered_destination():
    for x in load(DESTS,{"destinations":[]}).get("destinations",[]):
        if x.get("enabled") and x.get("chain")=="solana":
            return x.get("address")
    return None

def main():
    cfg=load(CFG,{})
    a=sys.argv[1] if len(sys.argv)>1 else "status"

    if a=="status":
        rc,g=run([sys.executable,"companyos/phase38broadcastctl","status"])
        print(json.dumps({
          "success":rc==0 and g.get("success"),
          "status":"phase38a_sol_canary_status",
          "config":cfg,
          "broadcast":g
        },indent=2))
        return 0 if rc==0 and g.get("success") else 1

    if a!="run":
        print(json.dumps({"success":False,"status":"usage","usage":"python companyos/phase38asolcanaryctl run"},indent=2))
        return 1

    dest=registered_destination()
    if not dest:
        print(json.dumps({"success":False,"status":"registered_solana_destination_missing"},indent=2))
        return 1

    # Confirm route is armed.
    rc,status=run([sys.executable,"companyos/phase38broadcastctl","status"])
    if rc!=0 or not status.get("success"):
        print(json.dumps({"success":False,"status":"phase38_status_failed","detail":status},indent=2))
        return 1

    sol_route=((status.get("canary_limits") or {}).get("solana") or {}).get("SOL") or {}
    if not status.get("global_broadcast_enabled") or not sol_route.get("enabled"):
        print(json.dumps({"success":False,"status":"sol_canary_not_armed"},indent=2))
        return 1

    # Guard canary limits.
    rc,guard=run([
      sys.executable,"companyos/phase38canaryguardctl",
      "solana","SOL",
      str(cfg["max_amount_native"]),
      str(cfg["max_amount_usd"]),
      dest
    ])
    if rc!=0 or not guard.get("success"):
        print(json.dumps({"success":False,"status":"canary_guard_blocked","detail":guard},indent=2))
        return 1

    # Use the already-proven controlled live Solana harness.
    rc,live=run([
      sys.executable,"companyos/solanalivetestctl",
      "live",
      dest,
      str(cfg["max_amount_native"]),
      str(cfg["max_amount_usd"])
    ])

    # Always disarm after test.
    run([sys.executable,"companyos/phase38broadcastctl","disarm","solana","SOL"])

    ok = rc==0 and live.get("success")
    print(json.dumps({
      "success":ok,
      "status":"phase38a_sol_canary_complete" if ok else "phase38a_sol_canary_failed",
      "destination":dest,
      "execution":live,
      "route_disarmed_after_test":True
    },indent=2))
    return 0 if ok else 1

raise SystemExit(main())
