#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " PHASE 38 - STAGED PRODUCTION BROADCAST ACTIVATION GATE"
echo "============================================================"

cat > "$MEM/phase38_broadcast_activation_config.json" <<'JSON'
{
  "enabled": true,
  "global_broadcast_enabled": false,
  "require_phase37_pass": true,
  "require_kill_switch_off": true,
  "require_registered_destination": true,
  "require_idempotency": true,
  "require_confirmation": true,
  "single_transaction_auto_limit_usd": 15000,
  "daily_total_limit_usd": 20000,
  "canary_limits": {
    "solana": {
      "SOL": {"enabled": false, "max_amount_native": 0.001, "max_amount_usd": 10},
      "USDT-SPL": {"enabled": false, "max_amount_native": 10, "max_amount_usd": 10},
      "USDC-SPL": {"enabled": false, "max_amount_native": 10, "max_amount_usd": 10}
    },
    "evm": {
      "ETH": {"enabled": false, "max_amount_native": 0.003, "max_amount_usd": 10},
      "USDT-ERC20": {"enabled": false, "max_amount_native": 10, "max_amount_usd": 10},
      "USDC-ERC20": {"enabled": false, "max_amount_native": 10, "max_amount_usd": 10}
    },
    "bitcoin": {
      "BTC": {"enabled": false, "max_amount_native": 0.00001, "max_amount_usd": 10}
    }
  },
  "promotion_requires_confirmed_canary": true
}
JSON

cat > "$MEM/phase38_route_state.json" <<'JSON'
{
  "routes": {},
  "confirmed_canaries": []
}
JSON

cat > "$AGENTS/phase38_broadcast_gate.py" <<'PY'
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
PY
chmod +x "$AGENTS/phase38_broadcast_gate.py"

cat > "$CTL/phase38broadcastctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase38_broadcast_gate.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase38broadcastctl"

cat > "$AGENTS/phase38_canary_guard.py" <<'PY'
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
PY
chmod +x "$AGENTS/phase38_canary_guard.py"

cat > "$CTL/phase38canaryguardctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase38_canary_guard.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase38canaryguardctl"

cat > "$CTL/phase38ctl" <<'PY'
#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
p=subprocess.run([sys.executable,"companyos/phase38broadcastctl","status"],cwd=r,text=True,capture_output=True)
try:d=json.loads(p.stdout)
except:d={"success":False,"status":"invalid_status_output","stdout":p.stdout,"stderr":p.stderr}
print(json.dumps({"success":p.returncode==0 and d.get("success"),"status":"phase38_ready","broadcast":d},indent=2))
raise SystemExit(0 if p.returncode==0 and d.get("success") else 1)
PY
chmod +x "$CTL/phase38ctl"

echo "[1/4] Compiling..."
python -m py_compile \
  "$AGENTS/phase38_broadcast_gate.py" \
  "$AGENTS/phase38_canary_guard.py" \
  "$CTL/phase38broadcastctl" \
  "$CTL/phase38canaryguardctl" \
  "$CTL/phase38ctl"

echo "[2/4] Forcing safe initial state..."
python "$CTL/phase38broadcastctl" emergency-off

echo "[3/4] Status..."
python "$CTL/phase38ctl"

echo "[4/4] Verifying..."
python - <<'PY'
import json
from pathlib import Path
r=Path.home()/"companyos"
errors=[]
cfg=json.loads((r/"ceo_memory"/"phase38_broadcast_activation_config.json").read_text())
p37=json.loads((r/"ceo_memory"/"phase37_safety_config.json").read_text())

if cfg.get("global_broadcast_enabled") is not False:
    errors.append("Phase38 must install with global broadcast disabled")
if p37.get("broadcast_enabled") is not False:
    errors.append("Phase37 broadcast must remain disabled")
if cfg.get("single_transaction_auto_limit_usd")!=15000:
    errors.append("single transaction limit mismatch")
if cfg.get("daily_total_limit_usd")!=20000:
    errors.append("daily limit mismatch")

for chain,routes in cfg.get("canary_limits",{}).items():
    for asset,row in routes.items():
        if row.get("enabled"):
            errors.append(f"{chain}:{asset} must install disarmed")

print("--------------------------------------------")
print("PHASE 38 BROADCAST ACTIVATION VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors: print("ERROR:",e)
if errors: raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 38 STAGED BROADCAST ACTIVATION GATE INSTALLED"
echo " GLOBAL BROADCAST: DISABLED"
echo " ALL LIVE ROUTES: DISARMED"
echo " CANARY CAPS: ENABLED"
echo " EXISTING \$15,000 SINGLE / \$20,000 DAILY POLICY: PRESERVED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/phase38ctl"
echo "  python companyos/phase38broadcastctl status"
echo "  python companyos/phase38broadcastctl arm-canary solana SOL"
echo "  python companyos/phase38broadcastctl emergency-off"
echo
echo "Do not arm a route until its canary transaction is ready."
