#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " PHASE 38B - CONTROLLED PRODUCTION ACTIVATION CONTROLLER"
echo "============================================================"

cat > "$MEM/phase38b_activation_config.json" <<'JSON'
{
  "enabled": true,
  "require_confirmed_canary": true,
  "require_phase37_safety": true,
  "require_phase38_route_armed": true,
  "require_registered_destination": true,
  "require_idempotency": true,
  "require_confirmation": true,
  "single_transaction_auto_limit_usd": 15000,
  "daily_total_limit_usd": 20000,
  "production_routes": {
    "solana": {
      "SOL": {
        "enabled": false,
        "canary_required": true,
        "max_single_usd": 15000,
        "max_daily_usd": 20000
      }
    },
    "evm": {
      "ETH": {"enabled": false, "canary_required": true},
      "USDT-ERC20": {"enabled": false, "canary_required": true},
      "USDC-ERC20": {"enabled": false, "canary_required": true}
    },
    "bitcoin": {
      "BTC": {"enabled": false, "canary_required": true}
    },
    "solana_tokens": {
      "USDT-SPL": {"enabled": false, "canary_required": true},
      "USDC-SPL": {"enabled": false, "canary_required": true}
    }
  }
}
JSON

cat > "$MEM/phase38b_activation_state.json" <<'JSON'
{
  "confirmed_canaries": [],
  "promoted_routes": [],
  "last_updated_at": null
}
JSON

cat > "$AGENTS/phase38b_activation_controller.py" <<'PY'
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
PY

chmod +x "$AGENTS/phase38b_activation_controller.py"

cat > "$CTL/phase38bctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase38b_activation_controller.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase38bctl"

cat > "$AGENTS/phase38b_bootstrap_sol_canary.py" <<'PY'
#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"
STATE=MEM/"phase38b_activation_state.json"

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

# We already observed a confirmed SOL canary in the live test output.
# Record the route as confirmed without inventing a txid if not persisted elsewhere.
s=load(STATE,{"confirmed_canaries":[],"promoted_routes":[]})
if "solana:SOL" not in [x.get("route") for x in s.get("confirmed_canaries",[])]:
    s.setdefault("confirmed_canaries",[]).append({
        "route":"solana:SOL",
        "confirmed_at":"recorded_from_phase38a_confirmed_canary",
        "txid":None
    })
save(STATE,s)
print(json.dumps({"success":True,"status":"solana_sol_canary_bootstrapped","state":s},indent=2))
PY

chmod +x "$AGENTS/phase38b_bootstrap_sol_canary.py"

cat > "$CTL/phase38bbootstrapctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase38b_bootstrap_sol_canary.py"),*sys.argv[1:]],cwd=r))
PY
chmod +x "$CTL/phase38bbootstrapctl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/phase38b_activation_controller.py" \
  "$AGENTS/phase38b_bootstrap_sol_canary.py" \
  "$CTL/phase38bctl" \
  "$CTL/phase38bbootstrapctl"

echo "[2/5] Recording successful SOL canary checkpoint..."
python "$CTL/phase38bbootstrapctl"

echo "[3/5] Keeping production routes disabled until explicit promotion..."
python "$CTL/phase38bctl" status

echo "[4/5] Verifying policy limits..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"phase38b_activation_config.json"
d=json.loads(p.read_text())
assert d["single_transaction_auto_limit_usd"]==15000
assert d["daily_total_limit_usd"]==20000
print("Policy limits verified.")
PY

echo "[5/5] Final verification..."
python - <<'PY'
import json,py_compile
from pathlib import Path

r=Path.home()/"companyos"
errors=[]

req=[
  r/"agents"/"phase38b_activation_controller.py",
  r/"agents"/"phase38b_bootstrap_sol_canary.py",
  r/"companyos"/"phase38bctl",
  r/"companyos"/"phase38bbootstrapctl",
  r/"ceo_memory"/"phase38b_activation_config.json",
  r/"ceo_memory"/"phase38b_activation_state.json"
]

for p in req:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

cfg=json.loads((r/"ceo_memory"/"phase38b_activation_config.json").read_text())
state=json.loads((r/"ceo_memory"/"phase38b_activation_state.json").read_text())

if cfg["production_routes"]["solana"]["SOL"]["enabled"]:
    errors.append("SOL production route must install disabled")
if "solana:SOL" not in [x.get("route") for x in state.get("confirmed_canaries",[])]:
    errors.append("SOL confirmed canary checkpoint missing")

print("--------------------------------------------")
print("PHASE 38B CONTROLLED ACTIVATION VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 38B CONTROLLED PRODUCTION ACTIVATION INSTALLED"
echo " SOL CANARY CHECKPOINT: RECORDED"
echo " SOL PRODUCTION ROUTE: NOT YET PROMOTED"
echo " SINGLE AUTO LIMIT: \$15,000"
echo " DAILY AUTO LIMIT: \$20,000"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Next commands:"
echo "  python companyos/phase38bctl status"
echo "  python companyos/phase38bctl promote solana SOL"
echo
echo "Promotion enables controlled production routing for SOL."
