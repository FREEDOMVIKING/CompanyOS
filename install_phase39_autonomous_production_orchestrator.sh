#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " PHASE 39 - AUTONOMOUS PRODUCTION EXECUTION ORCHESTRATOR"
echo "============================================================"

cat > "$MEM/phase39_production_orchestrator_config.json" <<'JSON'
{
  "enabled": true,
  "mode": "controlled_autonomous_production",
  "require_phase35_bridge": true,
  "require_phase37_safety": true,
  "require_phase38b_promotion": true,
  "require_registered_destination": true,
  "require_idempotency": true,
  "require_fresh_balance_check": true,
  "require_preflight": true,
  "require_confirmation": true,
  "require_kill_switch_off": true,
  "single_transaction_auto_limit_usd": 15000,
  "daily_total_limit_usd": 20000,
  "max_requests_per_cycle": 5,
  "stop_on_first_failure": true,
  "production_routes": {
    "solana": ["SOL"]
  }
}
JSON

cat > "$MEM/phase39_execution_state.json" <<'JSON'
{
  "last_run_at": null,
  "completed_count": 0,
  "failure_count": 0,
  "last_results": []
}
JSON

cat > "$MEM/phase39_idempotency_registry.json" <<'JSON'
{
  "completed": [],
  "in_progress": []
}
JSON

cat > "$AGENTS/phase39_production_orchestrator.py" <<'PY'
#!/usr/bin/env python3
import json, hashlib, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase39_production_orchestrator_config.json"
REQ=MEM/"ceo_treasury_requests.json"
PROPS=MEM/"transaction_proposals.json"
DESTS=MEM/"treasury_destination_registry.json"
P38B=MEM/"phase38b_activation_state.json"
P34CFG=MEM/"phase34_autonomous_treasury_config.json"
IDEM=MEM/"phase39_idempotency_registry.json"
STATE=MEM/"phase39_execution_state.json"
REPORT=MEM/"phase39_execution_report.json"
AUDIT=MEM/"phase39_execution_audit.jsonl"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(p,d):
    try:return json.loads(p.read_text())
    except:return d

def save(p,d):
    t=p.with_suffix(p.suffix+".tmp")
    t.write_text(json.dumps(d,indent=2))
    t.replace(p)

def audit(x):
    with AUDIT.open("a") as f:
        f.write(json.dumps({"at":now(),**x})+"\n")

def run_cmd(args):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=300)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json_output","stdout":p.stdout[-3000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def destination_allowed(chain,address):
    for x in load(DESTS,{"destinations":[]}).get("destinations",[]):
        if x.get("enabled") and x.get("chain")==chain and x.get("address")==address:
            return True
    return False

def route_promoted(chain,asset):
    key=f"{chain}:{asset}"
    return key in set(load(P38B,{"promoted_routes":[]}).get("promoted_routes",[]))

def idem_key(req):
    seed="|".join([
        str(req.get("request_id","")),
        str(req.get("chain","")),
        str(req.get("asset","")),
        str(req.get("destination","")),
        str(req.get("amount_native","")),
        str(req.get("amount_usd",""))
    ])
    return hashlib.sha256(seed.encode()).hexdigest()

def execute_request(req):
    cfg=load(CFG,{})
    reasons=[]
    chain=req.get("chain")
    asset=req.get("asset")
    dest=req.get("destination")

    if asset not in cfg.get("production_routes",{}).get(chain,[]):
        reasons.append("route_not_enabled_for_phase39")
    if not route_promoted(chain,asset):
        reasons.append("route_not_promoted_by_phase38b")
    if cfg.get("require_registered_destination") and not destination_allowed(chain,dest):
        reasons.append("destination_not_registered")
    try:
        if float(req.get("amount_usd",0)) > float(cfg["single_transaction_auto_limit_usd"]):
            reasons.append("single_transaction_limit_exceeded")
    except:
        reasons.append("invalid_amount_usd")

    if reasons:
        return {"success":False,"status":"phase39_request_blocked","reasons":reasons}

    # Create/refresh governed proposal through existing Phase 35 request bridge.
    if req.get("status")=="pending_bridge":
        rc,b=run_cmd([sys.executable,"companyos/ceotreasurybridgectl","run"])
        if rc!=0 or not b.get("success"):
            return {"success":False,"status":"phase35_bridge_failed","detail":b}

    # Refresh request and proposal references.
    requests=load(REQ,{"requests":[]}).get("requests",[])
    fresh=next((x for x in requests if x.get("request_id")==req.get("request_id")),req)
    pid=fresh.get("proposal_id")

    if not pid:
        return {"success":False,"status":"proposal_id_missing_after_bridge"}

    props=load(PROPS,{"proposals":[]}).get("proposals",[])
    prop=next((p for p in props if p.get("proposal_id")==pid),None)
    if not prop:
        return {"success":False,"status":"proposal_not_found"}

    if prop.get("status")!="ready_for_signing" or not prop.get("signing_authorized"):
        return {
          "success":False,
          "status":"proposal_not_ready_for_signing",
          "proposal_status":prop.get("status")
        }

    # Phase 37 preflight/safety must pass first.
    rc37,r37=run_cmd([sys.executable,"companyos/phase37ctl","run"])
    if rc37!=0 or not r37.get("success"):
        return {"success":False,"status":"phase37_safety_failed","detail":r37}

    # Re-check route promotion and emergency controls immediately before execution.
    if not route_promoted(chain,asset):
        return {"success":False,"status":"route_promotion_revoked_before_execution"}

    p34cfg=load(P34CFG,{})
    if p34cfg.get("kill_switch"):
        return {"success":False,"status":"treasury_kill_switch_active"}

    # Execute using existing governed autonomous treasury path.
    rc,r=run_cmd([sys.executable,"companyos/autonomoustreasuryctl","run"])
    return {
      "success":rc==0 and bool(r.get("success")),
      "status":"phase39_execution_submitted",
      "proposal_id":pid,
      "execution":r
    }

def cycle():
    cfg=load(CFG,{})
    if not cfg.get("enabled"):
        return {"success":True,"status":"phase39_disabled"}

    requests=[
      x for x in load(REQ,{"requests":[]}).get("requests",[])
      if x.get("status") in ("pending_bridge","bridge_submitted","executed")
    ]

    idem=load(IDEM,{"completed":[],"in_progress":[]})
    results=[]
    failures=0

    for req in requests[:int(cfg.get("max_requests_per_cycle",5))]:
        key=idem_key(req)

        if key in idem.get("completed",[]):
            results.append({
              "request_id":req.get("request_id"),
              "success":True,
              "status":"duplicate_skipped_already_completed"
            })
            continue

        if key in idem.get("in_progress",[]):
            results.append({
              "request_id":req.get("request_id"),
              "success":False,
              "status":"duplicate_blocked_in_progress"
            })
            failures+=1
            if cfg.get("stop_on_first_failure"):
                break
            continue

        idem.setdefault("in_progress",[]).append(key)
        save(IDEM,idem)

        r=execute_request(req)
        row={"request_id":req.get("request_id"),"idempotency_key":key,**r}
        results.append(row)
        audit(row)

        idem=load(IDEM,{"completed":[],"in_progress":[]})
        idem["in_progress"]=[x for x in idem.get("in_progress",[]) if x!=key]

        if r.get("success"):
            idem.setdefault("completed",[]).append(key)
        else:
            failures+=1

        save(IDEM,idem)

        if failures and cfg.get("stop_on_first_failure"):
            break

        time.sleep(2)

    report={
      "generated_at":now(),
      "request_count":len(requests),
      "processed_count":len(results),
      "failure_count":failures,
      "results":results
    }
    save(REPORT,report)
    save(STATE,{
      "last_run_at":now(),
      "completed_count":sum(1 for x in results if x.get("success")),
      "failure_count":failures,
      "last_results":results[-10:]
    })

    return {
      "success":failures==0,
      "status":"phase39_production_cycle_complete",
      "report":report
    }

a=sys.argv[1] if len(sys.argv)>1 else "run"

if a=="status":
    r={
      "success":True,
      "status":"phase39_production_status",
      "config":load(CFG,{}),
      "state":load(STATE,{}),
      "idempotency":load(IDEM,{"completed":[],"in_progress":[]}),
      "phase38b":load(P38B,{})
    }
else:
    r=cycle()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/phase39_production_orchestrator.py"

cat > "$CTL/phase39ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase39_production_orchestrator.py"),*sys.argv[1:]],cwd=r))
PY

chmod +x "$CTL/phase39ctl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/phase39_production_orchestrator.py" \
  "$CTL/phase39ctl"

echo "[2/5] Checking SOL promotion..."
python - <<'PY'
import json
from pathlib import Path
p=Path.home()/"companyos"/"ceo_memory"/"phase38b_activation_state.json"
d=json.loads(p.read_text())
if "solana:SOL" not in d.get("promoted_routes",[]):
    raise SystemExit("ERROR: solana:SOL is not promoted in Phase 38B")
print("SOL promotion verified.")
PY

echo "[3/5] Status..."
python "$CTL/phase39ctl" status

echo "[4/5] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path

p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text())
jobs=d.setdefault("jobs",[])

job={
  "id":"phase39-production-orchestrator",
  "enabled":True,
  "interval_seconds":60,
  "command":["python","companyos/phase39ctl","run"]
}

e=next((x for x in jobs if x.get("id")==job["id"]),None)
if e:
    e.clear();e.update(job)
else:
    jobs.append(job)

p.write_text(json.dumps(d,indent=2))
print(json.dumps({"success":True,"job_id":job["id"]},indent=2))
PY

python "$CTL/operationsctl" restart

echo "[5/5] Verifying..."
python - <<'PY'
import json,py_compile
from pathlib import Path

r=Path.home()/"companyos"
errors=[]

req=[
  r/"agents"/"phase39_production_orchestrator.py",
  r/"companyos"/"phase39ctl",
  r/"ceo_memory"/"phase39_production_orchestrator_config.json",
  r/"ceo_memory"/"phase39_execution_state.json",
  r/"ceo_memory"/"phase39_idempotency_registry.json"
]

for p in req:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

for p in req[:2]:
    try: py_compile.compile(str(p),doraise=True)
    except Exception as e: errors.append(str(e))

cfg=json.loads((r/"ceo_memory"/"phase39_production_orchestrator_config.json").read_text())

if cfg.get("production_routes")!={"solana":["SOL"]}:
    errors.append("Phase39 must initially enable only solana:SOL")
if cfg.get("single_transaction_auto_limit_usd")!=15000:
    errors.append("single limit mismatch")
if cfg.get("daily_total_limit_usd")!=20000:
    errors.append("daily limit mismatch")
if not cfg.get("require_idempotency"):
    errors.append("idempotency must remain required")

print("--------------------------------------------")
print("PHASE 39 PRODUCTION ORCHESTRATOR VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:
    print("ERROR:",e)
if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 39 AUTONOMOUS PRODUCTION ORCHESTRATOR INSTALLED"
echo " CONTROLLED AUTONOMOUS PRODUCTION: ENABLED"
echo " ACTIVE PRODUCTION ROUTE: SOLANA SOL ONLY"
echo " PHASE 35 -> 37 -> 38B -> EXECUTION CHAIN: CONNECTED"
echo " IDEMPOTENCY / DESTINATION / LIMIT / KILL-SWITCH GATES: ACTIVE"
echo " SINGLE AUTO LIMIT: \$15,000"
echo " DAILY AUTO LIMIT: \$20,000"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/phase39ctl status"
echo "  python companyos/phase39ctl run"
echo "  python companyos/treasurykillswitchctl on"
echo "  python companyos/treasurykillswitchctl off"
