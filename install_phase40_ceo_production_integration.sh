#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " PHASE 40 - CEO TO PRODUCTION TREASURY INTEGRATION"
echo "============================================================"

cat > "$MEM/phase40_ceo_production_config.json" <<'JSON'
{
  "enabled": true,
  "mode": "structured_decision_to_governed_execution",
  "require_explicit_treasury_action_type": true,
  "require_structured_fields": true,
  "require_phase38b_promotion": true,
  "require_registered_destination": true,
  "require_phase32_policy": true,
  "require_phase37_safety": true,
  "require_phase39_execution": true,
  "single_transaction_auto_limit_usd": 15000,
  "daily_total_limit_usd": 20000,
  "max_decisions_per_cycle": 5,
  "stop_on_first_failure": true,
  "allowed_production_routes": {
    "solana": ["SOL"]
  }
}
JSON

cat > "$MEM/ceo_production_decisions.json" <<'JSON'
{
  "decisions": []
}
JSON

cat > "$MEM/phase40_state.json" <<'JSON'
{
  "last_run_at": null,
  "processed_count": 0,
  "failure_count": 0,
  "last_results": []
}
JSON

cat > "$MEM/phase40_idempotency.json" <<'JSON'
{
  "processed_decision_ids": []
}
JSON

cat > "$AGENTS/phase40_ceo_production_bridge.py" <<'PY'
#!/usr/bin/env python3
import json, subprocess, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase40_ceo_production_config.json"
DECISIONS=MEM/"ceo_production_decisions.json"
IDEM=MEM/"phase40_idempotency.json"
STATE=MEM/"phase40_state.json"
REPORT=MEM/"phase40_report.json"
AUDIT=MEM/"phase40_audit.jsonl"

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

def normalize_decision_id(d):
    if d.get("decision_id"):
        return str(d["decision_id"])
    seed=json.dumps({
      "action_type":d.get("action_type"),
      "chain":d.get("chain"),
      "asset":d.get("asset"),
      "destination":d.get("destination"),
      "amount_native":d.get("amount_native"),
      "amount_usd":d.get("amount_usd"),
      "reason":d.get("reason")
    },sort_keys=True)
    return hashlib.sha256(seed.encode()).hexdigest()[:24]

def validate(d,cfg):
    reasons=[]
    if d.get("action_type")!="treasury_transfer":
        reasons.append("action_type_must_be_treasury_transfer")

    required=["chain","asset","destination","amount_native","amount_usd","reason"]
    for k in required:
        if d.get(k) in (None,""):
            reasons.append(f"missing_{k}")

    chain=d.get("chain")
    asset=d.get("asset")
    if asset not in cfg.get("allowed_production_routes",{}).get(chain,[]):
        reasons.append("route_not_enabled_for_phase40")

    try:
        usd=float(d.get("amount_usd",0))
        if usd<=0:
            reasons.append("amount_usd_must_be_positive")
        if usd>float(cfg["single_transaction_auto_limit_usd"]):
            reasons.append("single_transaction_limit_exceeded")
    except:
        reasons.append("invalid_amount_usd")

    try:
        native=float(d.get("amount_native",0))
        if native<=0:
            reasons.append("amount_native_must_be_positive")
    except:
        reasons.append("invalid_amount_native")

    return reasons

def enqueue_to_phase35(d):
    args=[
      sys.executable,
      "companyos/ceotreasuryrequestctl",
      "create",
      str(d["amount_usd"]),
      str(d["amount_native"]),
      d["asset"],
      d["chain"],
      d["destination"],
      d["reason"],
      str(d["decision_id"])
    ]
    return run_cmd(args)

def cycle():
    cfg=load(CFG,{})
    if not cfg.get("enabled"):
        return {"success":True,"status":"phase40_disabled"}

    q=load(DECISIONS,{"decisions":[]})
    idem=load(IDEM,{"processed_decision_ids":[]})
    processed=set(idem.get("processed_decision_ids",[]))

    pending=[
      d for d in q.get("decisions",[])
      if d.get("status","pending")=="pending"
    ]

    results=[]
    failures=0

    for d in pending[:int(cfg.get("max_decisions_per_cycle",5))]:
        d["decision_id"]=normalize_decision_id(d)

        if d["decision_id"] in processed:
            d["status"]="duplicate_skipped"
            row={
              "decision_id":d["decision_id"],
              "success":True,
              "status":"duplicate_skipped"
            }
            results.append(row)
            continue

        reasons=validate(d,cfg)
        if reasons:
            d["status"]="blocked"
            d["block_reasons"]=reasons
            row={
              "decision_id":d["decision_id"],
              "success":False,
              "status":"phase40_decision_blocked",
              "reasons":reasons
            }
            results.append(row)
            audit(row)
            failures+=1
            if cfg.get("stop_on_first_failure"):
                break
            continue

        rc,enq=enqueue_to_phase35(d)
        if rc!=0 or not enq.get("success"):
            d["status"]="enqueue_failed"
            row={
              "decision_id":d["decision_id"],
              "success":False,
              "status":"phase35_enqueue_failed",
              "detail":enq
            }
            results.append(row)
            audit(row)
            failures+=1
            if cfg.get("stop_on_first_failure"):
                break
            continue

        d["status"]="submitted_to_phase35"
        d["submitted_at"]=now()
        d["phase35_request"]=enq.get("request")

        processed.add(d["decision_id"])
        idem["processed_decision_ids"]=sorted(processed)
        save(IDEM,idem)

        row={
          "decision_id":d["decision_id"],
          "success":True,
          "status":"submitted_to_governed_production_pipeline",
          "phase35_request_id":(enq.get("request") or {}).get("request_id")
        }
        results.append(row)
        audit(row)

    q["updated_at"]=now()
    save(DECISIONS,q)

    # Run the existing governed pipeline only after successful submission.
    pipeline=None
    if any(x.get("success") and x.get("status")=="submitted_to_governed_production_pipeline" for x in results):
        rc35,r35=run_cmd([sys.executable,"companyos/ceotreasurybridgectl","run"])
        rc39,r39=run_cmd([sys.executable,"companyos/phase39ctl","run"])
        pipeline={
          "phase35":{"return_code":rc35,"result":r35},
          "phase39":{"return_code":rc39,"result":r39}
        }
        if rc35!=0 or rc39!=0 or not r35.get("success") or not r39.get("success"):
            failures+=1

    report={
      "generated_at":now(),
      "pending_count":len(pending),
      "processed_count":len(results),
      "failure_count":failures,
      "results":results,
      "pipeline":pipeline
    }
    save(REPORT,report)
    save(STATE,{
      "last_run_at":now(),
      "processed_count":len(results),
      "failure_count":failures,
      "last_results":results[-10:]
    })

    return {
      "success":failures==0,
      "status":"phase40_ceo_production_cycle_complete",
      "report":report
    }

a=sys.argv[1] if len(sys.argv)>1 else "run"

if a=="status":
    r={
      "success":True,
      "status":"phase40_ceo_production_status",
      "config":load(CFG,{}),
      "state":load(STATE,{}),
      "idempotency":load(IDEM,{"processed_decision_ids":[]}),
      "queue":load(DECISIONS,{"decisions":[]})
    }
else:
    r=cycle()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/phase40_ceo_production_bridge.py"

cat > "$CTL/phase40ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase40_ceo_production_bridge.py"),*sys.argv[1:]],cwd=r))
PY

chmod +x "$CTL/phase40ctl"

cat > "$AGENTS/phase40_decision_submitter.py" <<'PY'
#!/usr/bin/env python3
import json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
P=ROOT/"ceo_memory"/"ceo_production_decisions.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load():
    try:return json.loads(P.read_text())
    except:return {"decisions":[]}

def save(d):
    P.write_text(json.dumps(d,indent=2))

if len(sys.argv)<8:
    print(json.dumps({
      "success":False,
      "status":"usage",
      "usage":"submit CHAIN ASSET DESTINATION AMOUNT_NATIVE AMOUNT_USD REASON"
    },indent=2))
    raise SystemExit(1)

a=sys.argv[1]
if a!="submit":
    print(json.dumps({"success":False,"status":"unknown_action"},indent=2))
    raise SystemExit(1)

chain,asset,dest=sys.argv[2],sys.argv[3],sys.argv[4]
amount_native=float(sys.argv[5])
amount_usd=float(sys.argv[6])
reason=sys.argv[7]

decision_id=hashlib.sha256(
    f"{now()}|{chain}|{asset}|{dest}|{amount_native}|{amount_usd}|{reason}".encode()
).hexdigest()[:24]

row={
  "decision_id":decision_id,
  "created_at":now(),
  "source":"ceo_structured_decision",
  "action_type":"treasury_transfer",
  "chain":chain,
  "asset":asset,
  "destination":dest,
  "amount_native":amount_native,
  "amount_usd":amount_usd,
  "reason":reason,
  "status":"pending"
}

d=load()
d.setdefault("decisions",[]).append(row)
d["updated_at"]=now()
save(d)

print(json.dumps({
  "success":True,
  "status":"phase40_decision_queued",
  "decision":row
},indent=2))
PY

chmod +x "$AGENTS/phase40_decision_submitter.py"

cat > "$CTL/phase40decisionctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call([sys.executable,str(r/"agents"/"phase40_decision_submitter.py"),*sys.argv[1:]],cwd=r))
PY

chmod +x "$CTL/phase40decisionctl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/phase40_ceo_production_bridge.py" \
  "$AGENTS/phase40_decision_submitter.py" \
  "$CTL/phase40ctl" \
  "$CTL/phase40decisionctl"

echo "[2/5] Checking Phase 39..."
python "$CTL/phase39ctl" status >/dev/null
echo "Phase 39 available."

echo "[3/5] Status..."
python "$CTL/phase40ctl" status

echo "[4/5] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path

p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text())
jobs=d.setdefault("jobs",[])

job={
  "id":"phase40-ceo-production-integration",
  "enabled":True,
  "interval_seconds":60,
  "command":["python","companyos/phase40ctl","run"]
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
  r/"agents"/"phase40_ceo_production_bridge.py",
  r/"agents"/"phase40_decision_submitter.py",
  r/"companyos"/"phase40ctl",
  r/"companyos"/"phase40decisionctl",
  r/"ceo_memory"/"phase40_ceo_production_config.json",
  r/"ceo_memory"/"ceo_production_decisions.json",
  r/"ceo_memory"/"phase40_state.json",
  r/"ceo_memory"/"phase40_idempotency.json"
]

for p in req:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

for p in req[:4]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))

cfg=json.loads((r/"ceo_memory"/"phase40_ceo_production_config.json").read_text())

if cfg.get("allowed_production_routes")!={"solana":["SOL"]}:
    errors.append("Phase40 must initially allow only solana:SOL")
if cfg.get("single_transaction_auto_limit_usd")!=15000:
    errors.append("single limit mismatch")
if cfg.get("daily_total_limit_usd")!=20000:
    errors.append("daily limit mismatch")
if not cfg.get("require_phase39_execution"):
    errors.append("Phase39 execution must remain required")

print("--------------------------------------------")
print("PHASE 40 CEO PRODUCTION INTEGRATION VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:
    print("ERROR:",e)
if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 40 CEO TO PRODUCTION TREASURY INTEGRATION INSTALLED"
echo " STRUCTURED CEO TREASURY DECISIONS: CONNECTED"
echo " PHASE 35 -> 37 -> 38B -> 39 PIPELINE: CONNECTED"
echo " ACTIVE PRODUCTION ROUTE: SOLANA SOL ONLY"
echo " IDEMPOTENCY / DESTINATION / POLICY / KILL-SWITCH GATES: PRESERVED"
echo " SINGLE AUTO LIMIT: \$15,000"
echo " DAILY AUTO LIMIT: \$20,000"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/phase40ctl status"
echo "  python companyos/phase40ctl run"
echo "  python companyos/phase40decisionctl submit solana SOL DESTINATION AMOUNT_SOL AMOUNT_USD \"REASON\""
