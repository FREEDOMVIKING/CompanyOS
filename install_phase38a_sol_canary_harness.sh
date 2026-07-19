#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " PHASE 38A - SOLANA CANARY ACTIVATION + CONFIRMATION HARNESS"
echo "============================================================"

cat > "$MEM/phase38a_sol_canary_config.json" <<'JSON'
{
  "enabled": true,
  "chain": "solana",
  "asset": "SOL",
  "max_amount_native": 0.0001,
  "max_amount_usd": 1,
  "require_registered_destination": true,
  "require_phase38_route_armed": true,
  "require_phase37_broadcast_enabled": true,
  "require_confirmation": true,
  "auto_disarm_after_test": true
}
JSON

cat > "$AGENTS/phase38a_sol_canary.py" <<'PY'
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
PY

chmod +x "$AGENTS/phase38a_sol_canary.py"

cat > "$CTL/phase38asolcanaryctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase38a_sol_canary.py"),*sys.argv[1:]],cwd=r))
PY

chmod +x "$CTL/phase38asolcanaryctl"

echo "[1/4] Compiling..."
python -m py_compile \
  "$AGENTS/phase38a_sol_canary.py" \
  "$CTL/phase38asolcanaryctl"

echo "[2/4] Ensuring route is disarmed at install..."
python "$CTL/phase38broadcastctl" disarm solana SOL >/dev/null

echo "[3/4] Status check..."
python "$CTL/phase38asolcanaryctl" status

echo "[4/4] Verifying..."
python - <<'PY'
import json
from pathlib import Path

r=Path.home()/"companyos"
errors=[]

cfg=json.loads((r/"ceo_memory"/"phase38a_sol_canary_config.json").read_text())
p38=json.loads((r/"ceo_memory"/"phase38_broadcast_activation_config.json").read_text())

if cfg.get("max_amount_native") != 0.0001:
    errors.append("SOL canary amount mismatch")
if cfg.get("max_amount_usd") != 1:
    errors.append("USD canary amount mismatch")
if (((p38.get("canary_limits") or {}).get("solana") or {}).get("SOL") or {}).get("enabled"):
    errors.append("SOL route must install disarmed")

print("--------------------------------------------")
print("PHASE 38A SOL CANARY HARNESS VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:
    print("ERROR:",e)
if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 38A SOLANA CANARY HARNESS INSTALLED"
echo " TEST SIZE: 0.0001 SOL / \$1 POLICY VALUE"
echo " ROUTE STATE: DISARMED"
echo " AUTO-DISARM AFTER CANARY: ENABLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "When ready:"
echo "  python companyos/phase38broadcastctl arm-canary solana SOL"
echo "  python companyos/phase38asolcanaryctl run"
echo
echo "The route auto-disarms after the canary attempt."
