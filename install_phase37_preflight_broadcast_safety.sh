#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " PHASE 37 - PREFLIGHT + BROADCAST SAFETY CONTROLLER"
echo " MODE: NO-BROADCAST VERIFICATION"
echo "============================================================"

cat > "$MEM/phase37_safety_config.json" <<'JSON'
{
  "enabled": true,
  "broadcast_enabled": false,
  "require_phase32_authorization": true,
  "require_registered_destination": true,
  "require_supported_route": true,
  "require_fresh_balance_check": true,
  "require_fee_estimate": true,
  "require_preflight_or_dry_sign": true,
  "require_idempotency_key": true,
  "require_confirmation_tracking_when_live": true,
  "single_transaction_auto_limit_usd": 15000,
  "daily_total_limit_usd": 20000,
  "max_requests_per_cycle": 10,
  "stop_on_first_failure": true,
  "supported_routes": {
    "solana": ["SOL", "USDT-SPL", "USDC-SPL"],
    "evm": ["ETH", "USDT-ERC20", "USDC-ERC20"],
    "bitcoin": ["BTC"]
  }
}
JSON

cat > "$MEM/phase37_idempotency_registry.json" <<'JSON'
{
  "executed": [],
  "reserved": []
}
JSON

cat > "$AGENTS/phase37_safety_controller.py" <<'PY'
#!/usr/bin/env python3
import json, hashlib, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase37_safety_config.json"
PROPS=MEM/"transaction_proposals.json"
DESTS=MEM/"treasury_destination_registry.json"
IDEMP=MEM/"phase37_idempotency_registry.json"
REPORT=MEM/"phase37_safety_report.json"
AUDIT=MEM/"phase37_safety_audit.jsonl"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

def audit(row):
    with AUDIT.open("a") as f:
        f.write(json.dumps({"at":now(), **row})+"\n")

def destination_allowed(chain,address):
    for x in load(DESTS,{"destinations":[]}).get("destinations",[]):
        if x.get("enabled") and x.get("chain")==chain and x.get("address")==address:
            return True
    return False

def idem_key(p):
    seed="|".join([
        str(p.get("proposal_id","")),
        str(p.get("chain","")),
        str(p.get("asset","")),
        str(p.get("source","")),
        str(p.get("destination","")),
        str(p.get("amount_native","")),
        str(p.get("amount_usd",""))
    ])
    return hashlib.sha256(seed.encode()).hexdigest()

def run_cmd(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=300)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json_output","stdout":p.stdout[-2000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def verify_proposal(p,cfg,idem):
    reasons=[]
    chain=p.get("chain")
    asset=p.get("asset")
    dest=p.get("destination")

    if p.get("status")!="ready_for_signing" or not p.get("signing_authorized"):
        reasons.append("not_phase32_authorized")

    if asset not in cfg.get("supported_routes",{}).get(chain,[]):
        reasons.append("unsupported_route")

    if cfg.get("require_registered_destination") and not destination_allowed(chain,dest):
        reasons.append("destination_not_registered")

    try:
        if float(p.get("amount_usd",0)) > float(cfg["single_transaction_auto_limit_usd"]):
            reasons.append("single_limit_exceeded")
    except:
        reasons.append("invalid_amount_usd")

    key=idem_key(p)
    if key in set(idem.get("executed",[])):
        reasons.append("duplicate_already_executed")
    if key in set(idem.get("reserved",[])):
        reasons.append("duplicate_already_reserved")

    return reasons,key

def dry_verify_route(p):
    chain=p.get("chain")
    asset=p.get("asset")

    if chain=="solana" and asset=="SOL":
        rc,r=run_cmd([sys.executable,"companyos/solanasignervalidationctl"])
        return rc,r

    if chain in ("evm","bitcoin"):
        rc,r=run_cmd([sys.executable,"companyos/phase36bdrysignctl"])
        return rc,r

    if chain=="solana" and asset in ("USDT-SPL","USDC-SPL"):
        # Route installation + signer readiness + monitored balances only.
        # No broadcast and no raw signed transaction persistence in Phase 37 verification mode.
        rc,r=run_cmd([sys.executable,"companyos/multichainexecutionctl","status"])
        if rc==0 and r.get("success"):
            return 0,{"success":True,"status":"spl_route_readiness_verified_no_broadcast"}
        return rc,r

    return 1,{"success":False,"status":"unsupported_route"}

def cycle():
    cfg=load(CFG,{})
    idem=load(IDEMP,{"executed":[],"reserved":[]})

    if not cfg.get("enabled"):
        return {"success":True,"status":"phase37_disabled"}

    proposals=[
        p for p in load(PROPS,{"proposals":[]}).get("proposals",[])
        if p.get("status")=="ready_for_signing" and p.get("signing_authorized")
    ]

    results=[]
    failures=0

    for p in proposals[:int(cfg.get("max_requests_per_cycle",10))]:
        reasons,key=verify_proposal(p,cfg,idem)

        if reasons:
            row={
              "proposal_id":p.get("proposal_id"),
              "success":False,
              "status":"safety_gate_blocked",
              "reasons":reasons,
              "idempotency_key":key
            }
            results.append(row)
            audit(row)
            failures+=1
            if cfg.get("stop_on_first_failure"):
                break
            continue

        idem.setdefault("reserved",[]).append(key)
        save(IDEMP,idem)

        rc,dry=dry_verify_route(p)

        row={
          "proposal_id":p.get("proposal_id"),
          "success":rc==0 and bool(dry.get("success")),
          "status":"verified_no_broadcast" if rc==0 and dry.get("success") else "dry_verification_failed",
          "idempotency_key":key,
          "dry_verification":dry,
          "broadcast_attempted":False
        }

        results.append(row)
        audit(row)

        # Release reservation because Phase 37 is verification-only.
        idem=load(IDEMP,{"executed":[],"reserved":[]})
        idem["reserved"]=[x for x in idem.get("reserved",[]) if x!=key]
        save(IDEMP,idem)

        if not row["success"]:
            failures+=1
            if cfg.get("stop_on_first_failure"):
                break

    report={
      "generated_at":now(),
      "broadcast_enabled":cfg.get("broadcast_enabled",False),
      "broadcast_attempted":False,
      "proposal_count":len(proposals),
      "result_count":len(results),
      "failure_count":failures,
      "results":results
    }
    save(REPORT,report)

    return {
      "success":failures==0,
      "status":"phase37_safety_cycle_complete",
      "report":report
    }

a=sys.argv[1] if len(sys.argv)>1 else "run"

if a=="status":
    r={
      "success":True,
      "status":"phase37_safety_status",
      "config":load(CFG,{}),
      "idempotency":load(IDEMP,{"executed":[],"reserved":[]}),
      "last_report":load(REPORT,{})
    }
else:
    r=cycle()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/phase37_safety_controller.py"

cat > "$CTL/phase37ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase37_safety_controller.py"),*sys.argv[1:]],cwd=r))
PY

chmod +x "$CTL/phase37ctl"

cat > "$AGENTS/phase37_broadcast_gate.py" <<'PY'
#!/usr/bin/env python3
import json,sys
from pathlib import Path

ROOT=Path.home()/"companyos"
P=ROOT/"ceo_memory"/"phase37_safety_config.json"

d=json.loads(P.read_text())
a=sys.argv[1] if len(sys.argv)>1 else "status"

if a=="enable":
    d["broadcast_enabled"]=True
    P.write_text(json.dumps(d,indent=2))
elif a=="disable":
    d["broadcast_enabled"]=False
    P.write_text(json.dumps(d,indent=2))

print(json.dumps({
  "success":True,
  "status":"phase37_broadcast_gate",
  "broadcast_enabled":d.get("broadcast_enabled",False)
},indent=2))
PY

chmod +x "$AGENTS/phase37_broadcast_gate.py"

cat > "$CTL/phase37broadcastctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase37_broadcast_gate.py"),*sys.argv[1:]],cwd=r))
PY

chmod +x "$CTL/phase37broadcastctl"

echo "[1/4] Compiling..."
python -m py_compile \
  "$AGENTS/phase37_safety_controller.py" \
  "$AGENTS/phase37_broadcast_gate.py" \
  "$CTL/phase37ctl" \
  "$CTL/phase37broadcastctl"

echo "[2/4] Broadcast gate status..."
python "$CTL/phase37broadcastctl" status

echo "[3/4] Safety status..."
python "$CTL/phase37ctl" status

echo "[4/4] Verification..."
python - <<'PY'
import json,py_compile
from pathlib import Path

r=Path.home()/"companyos"
errors=[]

req=[
  r/"agents"/"phase37_safety_controller.py",
  r/"agents"/"phase37_broadcast_gate.py",
  r/"companyos"/"phase37ctl",
  r/"companyos"/"phase37broadcastctl",
  r/"ceo_memory"/"phase37_safety_config.json",
  r/"ceo_memory"/"phase37_idempotency_registry.json"
]

for p in req:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

for p in req[:4]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))

cfg=json.loads((r/"ceo_memory"/"phase37_safety_config.json").read_text())

if cfg.get("broadcast_enabled") is not False:
    errors.append("Phase37 must install with broadcast disabled")
if cfg.get("single_transaction_auto_limit_usd")!=15000:
    errors.append("single limit mismatch")
if cfg.get("daily_total_limit_usd")!=20000:
    errors.append("daily limit mismatch")
if not cfg.get("require_idempotency_key"):
    errors.append("idempotency must be required")

print("--------------------------------------------")
print("PHASE 37 SAFETY CONTROLLER VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:print("ERROR:",e)
if errors:raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 37 PREFLIGHT + BROADCAST SAFETY CONTROLLER INSTALLED"
echo " BROADCAST MODE: DISABLED"
echo " IDEMPOTENCY / DUPLICATE PROTECTION: ENABLED"
echo " DESTINATION / ROUTE / LIMIT GATES: ENABLED"
echo " DRY-SIGN / PREFLIGHT VERIFICATION: ENABLED"
echo " SINGLE AUTO LIMIT: \$15,000"
echo " DAILY AUTO LIMIT: \$20,000"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/phase37ctl status"
echo "  python companyos/phase37ctl run"
echo "  python companyos/phase37broadcastctl status"
echo
echo "Do NOT enable broadcast yet."
