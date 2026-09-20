#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
R="$HOME/.companyos_runtime"
Q="$R/task_queue"
OUT="$R/v38_failure_forensics.json"

echo "===== COMPANYOS V38 FAILURE FORENSICS ====="
echo "READ_ONLY=YES"
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTARTED=NO"
echo "FINANCE_CONNECTORS_CHANGED=NO"

python - <<'PY'
from pathlib import Path
import json, collections, time, re
root=Path.home()/".companyos_runtime"
q=root/"task_queue"

def load():
    rows=[]
    for p in q.glob("*.json"):
        try:
            x=json.loads(p.read_text())
            if isinstance(x,dict):
                x["_file"]=str(p)
                rows.append(x)
        except Exception:
            pass
    return rows

def state(x):
    return str(x.get("state") or x.get("status") or "").upper()

def err(x):
    vals=[]
    for k in ("error","last_error","failure_reason","reason","message","detail","exception"):
        v=x.get(k)
        if v not in (None,""):
            vals.append(f"{k}={v}")
    # inspect common nested metadata/result without dumping huge payloads
    for nk in ("result","metadata","execution","last_result"):
        v=x.get(nk)
        if isinstance(v,dict):
            for k in ("error","last_error","failure_reason","reason","message","exception"):
                z=v.get(k)
                if z not in (None,""):
                    vals.append(f"{nk}.{k}={z}")
    return " | ".join(vals)[:1200] or "<NO_RECORDED_ERROR>"

before=load()
bfailed={str(x.get("id") or x.get("task_id") or x["_file"]):x for x in before if state(x)=="FAILED"}
print("BASELINE", collections.Counter(state(x) for x in before))
print("BASE_FAILED",len(bfailed))
print("OBSERVE=45s")
time.sleep(45)
after=load()
afailed={str(x.get("id") or x.get("task_id") or x["_file"]):x for x in after if state(x)=="FAILED"}
new=[x for k,x in afailed.items() if k not in bfailed]
print("AFTER",collections.Counter(state(x) for x in after))
print("NEW_FAILED",len(new))

bytype=collections.Counter(str(x.get("task_type") or x.get("type") or "<none>") for x in new)
byerr=collections.Counter(err(x) for x in new)
print("\n===== NEW FAILURES BY TASK TYPE =====")
for k,v in bytype.most_common(): print(v,k)
print("\n===== NEW FAILURES BY RECORDED ERROR =====")
for k,v in byerr.most_common(20): print(v,repr(k))

print("\n===== SAMPLE NEW FAILED RECORDS =====")
for x in new[:12]:
    print(json.dumps({
      "id":x.get("id") or x.get("task_id"),
      "type":x.get("task_type") or x.get("type"),
      "state":state(x),
      "attempts":x.get("attempts") or x.get("attempt_count"),
      "error":err(x),
      "file":x["_file"],
    },default=str))

# Search runtime logs/state text for exception signatures, bounded to recent/small files.
print("\n===== RECENT RUNTIME ERROR SIGNATURES =====")
candidates=[]
for base in (root, root/"logs"):
    if base.exists():
        for p in base.rglob("*"):
            try:
                if p.is_file() and p.stat().st_size <= 5_000_000:
                    candidates.append(p)
            except: pass
candidates=sorted(set(candidates), key=lambda p:p.stat().st_mtime if p.exists() else 0, reverse=True)[:80]
pat=re.compile(r"(Traceback|Exception|Error|failed|failure|timeout|lease)",re.I)
hits=[]
for p in candidates:
    try:
        lines=p.read_text(errors="replace").splitlines()
    except: continue
    for line in lines[-500:]:
        if pat.search(line):
            hits.append((str(p),line[:1000]))
for f,line in hits[-60:]:
    print(f"{f}: {line}")

report={
 "baseline_states":dict(collections.Counter(state(x) for x in before)),
 "after_states":dict(collections.Counter(state(x) for x in after)),
 "new_failed":len(new),
 "new_failed_by_type":dict(bytype),
 "new_failed_by_error":dict(byerr),
 "samples":[{"id":x.get("id") or x.get("task_id"),"type":x.get("task_type") or x.get("type"),
             "attempts":x.get("attempts") or x.get("attempt_count"),"error":err(x),"file":x["_file"]} for x in new[:30]],
}
(root/"v38_failure_forensics.json").write_text(json.dumps(report,indent=2,default=str))
print("\nREPORT="+str(root/"v38_failure_forensics.json"))
PY

echo
echo "===== SOURCE PATH FORENSICS ====="
grep -RInE --include='*.py' \
  'queue\.fail|\.fail\(|handler\(task\)|leased_execution|ExecutionGuard|run_bounded|retry_delay|FAILED' \
  companyos/runtime 2>/dev/null | head -n 180 || true

echo
echo "===== V34-V36 REGRESSION ====="
python -m pytest -q \
  tests/test_v34_worker_lease_store.py \
  tests/test_v35_1_dispatcher_ast_contract.py \
  tests/test_v36_live_recovery_qualification.py 2>/dev/null || {
    echo "REGRESSION_TEST_PATH_VARIANCE_OR_FAILURE=YES"
    echo "Continuing: V38 is diagnostic/read-only."
  }

echo
echo "===== V38 COMPLETE ====="
echo "READ_ONLY=YES"
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTARTED=NO"
echo "NEXT=use NEW_FAILURES_BY_RECORDED_ERROR plus source path to build exact V39 repair"
