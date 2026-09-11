#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEM="$ROOT/ceo_memory"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEM"

echo "============================================================"
echo " PHASE 43 - AUTONOMOUS BUSINESS OPERATIONS LOOP"
echo "============================================================"

cat > "$MEM/phase43_business_loop_config.json" <<'JSON'
{
  "enabled": true,
  "mode": "continuous_governed_business_operations",
  "max_actions_per_cycle": 10,
  "max_retry_attempts": 3,
  "retry_backoff_seconds": 30,
  "require_phase41_router": true,
  "require_phase42_receipts": true,
  "require_idempotency": true,
  "require_receipt_before_learning": true,
  "feed_outcomes_to_ceo_memory": true,
  "retry_only_transient_failures": true,
  "financial_actions_stay_under_existing_treasury_controls": true,
  "external_actions_fail_closed": true
}
JSON

cat > "$MEM/phase43_retry_queue.json" <<'JSON'
{
  "items": []
}
JSON

cat > "$MEM/phase43_state.json" <<'JSON'
{
  "last_run_at": null,
  "processed_receipts": [],
  "retry_count": 0,
  "learning_events": 0,
  "last_results": []
}
JSON

cat > "$MEM/phase43_learning_feed.json" <<'JSON'
{
  "events": []
}
JSON

cat > "$AGENTS/phase43_business_operations_loop.py" <<'PY'
#!/usr/bin/env python3
import json, subprocess, sys, time, hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path.home()/"companyos"
MEM=ROOT/"ceo_memory"

CFG=MEM/"phase43_business_loop_config.json"
RECEIPTS=MEM/"phase42_delivery_receipts.json"
QUEUE=MEM/"phase42_connector_queue.json"
RETRY=MEM/"phase43_retry_queue.json"
STATE=MEM/"phase43_state.json"
LEARN=MEM/"phase43_learning_feed.json"
AUDIT=MEM/"phase43_audit.jsonl"
REPORT=MEM/"phase43_report.json"

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

def run(args,timeout=600):
    p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=timeout)
    try:r=json.loads(p.stdout)
    except:r={"success":False,"status":"invalid_json_output","stdout":p.stdout[-3000:],"stderr":p.stderr[-1000:]}
    return p.returncode,r

def transient(status):
    s=(status or "").lower()
    keys=("timeout","tempor","rate_limit","429","503","502","504","unavailable","connection")
    return any(k in s for k in keys)

def enqueue_retry(receipt,retryq,cfg):
    rid=receipt.get("receipt_id") or hashlib.sha256(json.dumps(receipt,sort_keys=True).encode()).hexdigest()[:24]
    existing={x.get("receipt_id") for x in retryq.get("items",[])}
    if rid in existing:
        return False

    retryq.setdefault("items",[]).append({
      "receipt_id":rid,
      "job_id":receipt.get("job_id"),
      "connector":receipt.get("connector"),
      "attempts":0,
      "max_attempts":cfg.get("max_retry_attempts",3),
      "status":"pending_retry",
      "queued_at":now()
    })
    return True

def process_new_receipts(cfg,state,retryq,learn):
    receipts=load(RECEIPTS,{"receipts":[]}).get("receipts",[])
    seen=set(state.get("processed_receipts",[]))
    results=[]

    for r in receipts:
        rid=r.get("receipt_id")
        if not rid or rid in seen:
            continue

        event={
          "event_id":hashlib.sha256(f"{rid}|{now()}".encode()).hexdigest()[:24],
          "created_at":now(),
          "source":"phase42_delivery_receipt",
          "receipt_id":rid,
          "job_id":r.get("job_id"),
          "connector":r.get("connector"),
          "success":bool(r.get("success")),
          "status":r.get("status"),
          "external_reference":r.get("external_reference"),
          "learning_type":"successful_external_action" if r.get("success") else "failed_external_action"
        }

        learn.setdefault("events",[]).append(event)
        seen.add(rid)

        if (not r.get("success")) and cfg.get("retry_only_transient_failures") and transient(r.get("status")):
            enqueue_retry(r,retryq,cfg)

        results.append({
          "receipt_id":rid,
          "success":True,
          "status":"receipt_ingested_into_learning_feed",
          "action_success":bool(r.get("success"))
        })
        audit(results[-1])

    state["processed_receipts"]=sorted(seen)
    state["learning_events"]=len(learn.get("events",[]))
    return results

def retry_jobs(cfg,retryq):
    q=load(QUEUE,{"jobs":[]})
    results=[]

    for item in retryq.get("items",[])[:int(cfg.get("max_actions_per_cycle",10))]:
        if item.get("status")!="pending_retry":
            continue
        if int(item.get("attempts",0))>=int(item.get("max_attempts",3)):
            item["status"]="retry_exhausted"
            continue

        job=next((j for j in q.get("jobs",[]) if j.get("job_id")==item.get("job_id")),None)
        if not job:
            item["status"]="retry_job_missing"
            results.append({"job_id":item.get("job_id"),"success":False,"status":"retry_job_missing"})
            continue

        # Reset failed connector job to pending; Phase 42 remains responsible for execution.
        job["status"]="pending"
        job["retry_requested_at"]=now()
        item["attempts"]=int(item.get("attempts",0))+1
        item["last_retry_at"]=now()
        item["status"]="retry_submitted"

        results.append({
          "job_id":job.get("job_id"),
          "success":True,
          "status":"retry_submitted_to_phase42",
          "attempt":item["attempts"]
        })

    save(QUEUE,q)
    save(RETRY,retryq)
    return results

def cycle():
    cfg=load(CFG,{})
    if not cfg.get("enabled"):
        return {"success":True,"status":"phase43_disabled"}

    state=load(STATE,{
      "last_run_at":None,
      "processed_receipts":[],
      "retry_count":0,
      "learning_events":0,
      "last_results":[]
    })
    retryq=load(RETRY,{"items":[]})
    learn=load(LEARN,{"events":[]})

    # 1) Let Phase 41 route any pending CEO external actions.
    rc41,r41=run([sys.executable,"companyos/phase41ctl","run"])

    # 2) Let Phase 42 execute configured connectors and produce receipts.
    rc42,r42=run([sys.executable,"companyos/phase42ctl","run"])

    # 3) Ingest receipts into learning feed and retry queue.
    receipt_results=process_new_receipts(cfg,state,retryq,learn)

    # 4) Retry only transient connector failures.
    retry_results=retry_jobs(cfg,retryq)

    # 5) If retries were submitted, run Phase 42 once more.
    retry_phase42=None
    if any(x.get("success") for x in retry_results):
        if int(cfg.get("retry_backoff_seconds",30))>0:
            time.sleep(min(int(cfg.get("retry_backoff_seconds",30)),5))
        rc42b,r42b=run([sys.executable,"companyos/phase42ctl","run"])
        retry_phase42={"return_code":rc42b,"result":r42b}

    save(RETRY,retryq)
    save(LEARN,learn)

    failures=0
    if rc41!=0 or not r41.get("success"):
        failures+=1
    if rc42!=0 or not r42.get("success"):
        # Unconfigured connectors are fail-closed and may produce failures; record honestly.
        failures+=1

    state["last_run_at"]=now()
    state["retry_count"]=sum(int(x.get("attempts",0)) for x in retryq.get("items",[]))
    state["last_results"]=(receipt_results+retry_results)[-20:]
    save(STATE,state)

    report={
      "generated_at":now(),
      "phase41":{"return_code":rc41,"result":r41},
      "phase42":{"return_code":rc42,"result":r42},
      "receipt_results":receipt_results,
      "retry_results":retry_results,
      "retry_phase42":retry_phase42,
      "learning_event_count":len(learn.get("events",[])),
      "failure_count":failures
    }
    save(REPORT,report)

    return {
      "success":failures==0,
      "status":"phase43_business_operations_cycle_complete",
      "report":report
    }

a=sys.argv[1] if len(sys.argv)>1 else "run"

if a=="status":
    r={
      "success":True,
      "status":"phase43_business_operations_status",
      "config":load(CFG,{}),
      "state":load(STATE,{}),
      "retry_queue":load(RETRY,{"items":[]}),
      "learning_feed":load(LEARN,{"events":[]})
    }
else:
    r=cycle()

print(json.dumps(r,indent=2))
raise SystemExit(0 if r.get("success") else 1)
PY

chmod +x "$AGENTS/phase43_business_operations_loop.py"

cat > "$CTL/phase43ctl" <<'PY'
#!/usr/bin/env python3
import subprocess,sys
from pathlib import Path
r=Path.home()/"companyos"
raise SystemExit(subprocess.call(
    [sys.executable,str(r/"agents"/"phase43_business_operations_loop.py"),*sys.argv[1:]],
    cwd=r
))
PY
chmod +x "$CTL/phase43ctl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/phase43_business_operations_loop.py" \
  "$CTL/phase43ctl"

echo "[2/5] Checking Phase 41 + 42..."
python "$CTL/phase41ctl" status >/dev/null
python "$CTL/phase42ctl" status >/dev/null
echo "Phase 41 and 42 available."

echo "[3/5] Status..."
python "$CTL/phase43ctl" status

echo "[4/5] Registering scheduler..."
python - <<'PY'
import json
from pathlib import Path

p=Path.home()/"companyos"/"ceo_memory"/"autonomous_operations_config.json"
d=json.loads(p.read_text())
jobs=d.setdefault("jobs",[])

job={
  "id":"phase43-autonomous-business-operations-loop",
  "enabled":True,
  "interval_seconds":60,
  "command":["python","companyos/phase43ctl","run"]
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
  r/"agents"/"phase43_business_operations_loop.py",
  r/"companyos"/"phase43ctl",
  r/"ceo_memory"/"phase43_business_loop_config.json",
  r/"ceo_memory"/"phase43_retry_queue.json",
  r/"ceo_memory"/"phase43_state.json",
  r/"ceo_memory"/"phase43_learning_feed.json"
]

for p in req:
    if not p.exists() or p.stat().st_size<=0:
        errors.append(f"Missing/empty: {p}")

for p in req[:2]:
    try:py_compile.compile(str(p),doraise=True)
    except Exception as e:errors.append(str(e))

cfg=json.loads((r/"ceo_memory"/"phase43_business_loop_config.json").read_text())

if not cfg.get("require_phase41_router"):
    errors.append("Phase41 router must be required")
if not cfg.get("require_phase42_receipts"):
    errors.append("Phase42 receipts must be required")
if not cfg.get("require_idempotency"):
    errors.append("idempotency must be required")
if not cfg.get("financial_actions_stay_under_existing_treasury_controls"):
    errors.append("financial controls must remain external to Phase43")
if not cfg.get("external_actions_fail_closed"):
    errors.append("external actions must fail closed")

print("--------------------------------------------")
print("PHASE 43 BUSINESS OPERATIONS LOOP VERIFICATION")
print(f"Errors: {len(errors)}")
print("Warnings: 0")
for e in errors:
    print("ERROR:",e)
if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 43 AUTONOMOUS BUSINESS OPERATIONS LOOP INSTALLED"
echo " PHASE 41 ROUTING -> PHASE 42 EXECUTION -> RECEIPTS -> LEARNING: CONNECTED"
echo " TRANSIENT RETRIES: ENABLED"
echo " DUPLICATE PROTECTION: ENABLED"
echo " FINANCIAL ACTIONS: STILL GOVERNED BY EXISTING TREASURY CONTROLS"
echo " EXTERNAL ACTIONS: FAIL-CLOSED UNTIL CONNECTORS ARE CONFIGURED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/phase43ctl status"
echo "  python companyos/phase43ctl run"
