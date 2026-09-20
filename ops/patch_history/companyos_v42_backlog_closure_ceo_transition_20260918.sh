#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
R="$HOME/.companyos_runtime"; Q="$R/task_queue"; TS="$(date +%Y%m%d_%H%M%S)"
OUT="$R/v42_backlog_closure_${TS}.log"
mkdir -p "$R"
exec > >(tee -a "$OUT") 2>&1

echo "===== COMPANYOS V42 BACKLOG CLOSURE + CEO TRANSITION ====="
echo "MODE=QUALIFY_AND_CLASSIFY"
echo "QUEUE_RECORDS_DELETED=0"
echo "FAILED_TASKS_MUTATED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "SUPERVISOR_RESTARTED=NO"

snap () {
python - "$Q" <<'PY'
import json,sys,collections
from pathlib import Path
c=collections.Counter(); types=collections.Counter(); reasons=collections.Counter()
for f in Path(sys.argv[1]).glob("*.json"):
 try:
  d=json.loads(f.read_text()); st=str(d.get("state","UNKNOWN")).upper()
  c[st]+=1
  if st=="QUEUED": types[str(d.get("task_type") or d.get("type") or "unknown")]+=1
  if st=="FAILED":
   e=str(d.get("last_error") or d.get("error") or "")
   if e: reasons[e[:160]]+=1
 except Exception: c["UNREADABLE"]+=1
print("STATES",dict(c))
print("QUEUED_TYPES",dict(types))
print("TOP_FAILURES",reasons.most_common(5))
PY
}
num () {
python - "$Q" "$1" <<'PY'
import json,sys
from pathlib import Path
n=0
for f in Path(sys.argv[1]).glob("*.json"):
 try:
  if str(json.loads(f.read_text()).get("state","")).upper()==sys.argv[2]: n+=1
 except: pass
print(n)
PY
}

echo "===== SINGLETON ====="
SUP=$(pgrep -af 'companyos/runtime/service_supervisor.py'|grep -v grep|wc -l||true)
CON=$(pgrep -af 'continuous_goal_runtime'|grep -v grep|wc -l||true)
echo "SUPERVISOR_COUNT=$SUP CONTINUOUS_COUNT=$CON"
[ "$SUP" -eq 1 ] && [ "$CON" -eq 1 ] || { echo "V42_ABORT=SINGLETON"; exit 42; }

echo "===== REGRESSION ====="
python -m pytest -q tests/test_v39_dispatch_result_repair.py tests/test_v36_live_recovery_qualification.py tests/test_v34_worker_lease_store.py
echo "REGRESSION=PASS"

echo "===== BASELINE ====="; snap
C0=$(num COMPLETED); F0=$(num FAILED); Q0=$(num QUEUED)

echo "===== LIVE BACKLOG CLOSURE WATCH ====="
for t in 60 120 180 240 300; do
 sleep 60
 C=$(num COMPLETED); F=$(num FAILED); QQ=$(num QUEUED)
 echo "T+$t COMPLETED=$C FAILED=$F QUEUED=$QQ completed_delta=$((C-C0)) failed_delta=$((F-F0)) queued_delta=$((QQ-Q0))"
done

C1=$(num COMPLETED); F1=$(num FAILED); Q1=$(num QUEUED)
echo "FINAL_COMPLETED_DELTA=$((C1-C0))"
echo "FINAL_FAILED_DELTA=$((F1-F0))"
echo "FINAL_QUEUED_DELTA=$((Q1-Q0))"

echo "===== HISTORICAL FAILURE RECOVERY CLASSIFICATION (READ ONLY) ====="
python - "$Q" "$R/v42_failed_recovery_candidates_${TS}.json" <<'PY'
import json,sys,collections
from pathlib import Path
q=Path(sys.argv[1]); out=Path(sys.argv[2]); rows=[]; classes=collections.Counter()
for f in q.glob("*.json"):
 try:
  d=json.loads(f.read_text())
  if str(d.get("state","")).upper()!="FAILED": continue
  e=str(d.get("last_error") or d.get("error") or "")
  low=e.lower()
  if "name 'result' is not defined" in low: cl="code_bug_now_repaired"
  elif any(x in low for x in ("timeout","lease","temporar","connection")): cl="transient_review"
  elif any(x in low for x in ("permission","approval","awaiting_external","certificate")): cl="external_gate_do_not_auto_retry"
  else: cl="manual_classification"
  classes[cl]+=1
  rows.append({"file":str(f),"task_id":d.get("task_id") or d.get("id"),"task_type":d.get("task_type") or d.get("type"),"classification":cl,"error":e[:500]})
 except Exception: pass
out.write_text(json.dumps({"counts":dict(classes),"candidates":rows},indent=2))
print("FAILURE_CLASSES="+json.dumps(dict(classes),sort_keys=True))
print("RECOVERY_CANDIDATE_REPORT="+str(out))
print("FAILED_TASKS_MUTATED=0")
PY

echo "===== DEPENDENCY / CEO PIPELINE SAMPLE ====="
python - "$Q" <<'PY'
import json,sys,collections
from pathlib import Path
stage=collections.Counter(); state_by_type=collections.Counter()
for f in Path(sys.argv[1]).glob("*.json"):
 try:
  d=json.loads(f.read_text()); st=str(d.get("state","UNKNOWN")).upper()
  ty=str(d.get("task_type") or d.get("type") or "unknown")
  state_by_type[(ty,st)]+=1
  dep=d.get("depends_on_stage")
  if dep: stage[(str(dep),st)]+=1
 except: pass
print("TYPE_STATE_COUNTS",dict((f"{a}:{b}",n) for (a,b),n in state_by_type.items()))
print("DEPENDENCY_STATE_COUNTS",dict((f"{a}:{b}",n) for (a,b),n in stage.items()))
PY

echo "===== FINAL HEALTH ====="; snap
SUP2=$(pgrep -af 'companyos/runtime/service_supervisor.py'|grep -v grep|wc -l||true)
CON2=$(pgrep -af 'continuous_goal_runtime'|grep -v grep|wc -l||true)
echo "SUPERVISOR_COUNT=$SUP2 CONTINUOUS_COUNT=$CON2"

PASS=YES
[ "$SUP2" -eq 1 ] || PASS=NO
[ "$CON2" -eq 1 ] || PASS=NO
[ "$((C1-C0))" -gt 0 ] || PASS=NO
[ "$((F1-F0))" -eq 0 ] || PASS=NO
if [ "$PASS" = YES ]; then
 echo "V42_EXECUTION_CORE_QUALIFIED=PASS"
 echo "CEO_TRANSITION_READY=YES"
else
 echo "V42_EXECUTION_CORE_QUALIFIED=NEEDS_DIAGNOSIS"
 echo "CEO_TRANSITION_READY=NO"
fi
echo "QUEUE_RECORDS_DELETED=0"
echo "FAILED_TASKS_MUTATED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "REPORT=$OUT"
