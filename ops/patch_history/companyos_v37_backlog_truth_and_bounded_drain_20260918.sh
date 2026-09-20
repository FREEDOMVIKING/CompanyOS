#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
cd "$HOME/companyos"
RT="$HOME/.companyos_runtime"; B="$RT/backups/v37_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$B"
echo "===== COMPANYOS V37 BACKLOG TRUTH + BOUNDED DRAIN ====="

grep -q 'V35_1_FENCED_HANDLER_CALL' companyos/runtime/autonomous_task_dispatcher.py || { echo "PREFLIGHT_FAIL=V35.1_missing"; exit 20; }
python -m py_compile companyos/runtime/autonomous_task_dispatcher.py companyos/runtime/lease_execution_guard.py
echo "PREFLIGHT=PASS"

cat > companyos/runtime/backlog_truth_probe.py <<'PY'
from __future__ import annotations
import json, collections, time
from pathlib import Path

def probe(root=None):
    root=Path(root or (Path.home()/".companyos_runtime"/"task_queue"))
    rows=[]; bad=0
    for p in root.iterdir() if root.exists() else []:
        if p.suffix!=".json": continue
        try: rows.append(json.loads(p.read_text()))
        except Exception: bad+=1
    states=collections.Counter(str(x.get("state","UNKNOWN")).upper() for x in rows)
    types=collections.Counter(str(x.get("task_type") or x.get("type") or "UNKNOWN") for x in rows if str(x.get("state","")).upper()=="QUEUED")
    completed={(str(x.get("goal_id","")),str(x.get("stage") or x.get("task_type") or x.get("type") or "")) for x in rows if str(x.get("state","")).upper()=="COMPLETED"}
    reasons=collections.Counter(); ready=[]
    for x in rows:
        if str(x.get("state","")).upper()!="QUEUED": continue
        typ=str(x.get("task_type") or x.get("type") or "")
        dep=x.get("depends_on_stage")
        goal=str(x.get("goal_id",""))
        attempts=int(x.get("attempts",0) or 0)
        maxa=int(x.get("max_attempts",3) or 3)
        if attempts>=maxa: reasons["attempts_exhausted"]+=1
        elif dep and (goal,str(dep)) not in completed: reasons["dependency_blocked"]+=1
        elif typ not in {"research","planning","build"}: reasons["unsupported_type"]+=1
        else:
            reasons["execution_ready"]+=1
            if len(ready)<100: ready.append(str(x.get("task_id") or x.get("id") or ""))
    return {"states":dict(states),"queued_types":dict(types),"reasons":dict(reasons),"unreadable":bad,"ready_sample":ready,"ts":time.time()}
if __name__=="__main__": print(json.dumps(probe(),indent=2,sort_keys=True))
PY

cat > tests/test_v37_backlog_truth_probe.py <<'PY'
import json,tempfile
from pathlib import Path
from companyos.runtime.backlog_truth_probe import probe
def test_classification():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)
        rows=[
          {"task_id":"c","goal_id":"g","task_type":"research","stage":"research","state":"COMPLETED"},
          {"task_id":"a","goal_id":"g","task_type":"planning","state":"QUEUED","depends_on_stage":"research"},
          {"task_id":"b","goal_id":"x","task_type":"planning","state":"QUEUED","depends_on_stage":"research"},
          {"task_id":"z","goal_id":"g","task_type":"weird","state":"QUEUED"}]
        for i,r in enumerate(rows):(p/f"{i}.json").write_text(json.dumps(r))
        x=probe(p)
        assert x["reasons"]["execution_ready"]==1
        assert x["reasons"]["dependency_blocked"]==1
        assert x["reasons"]["unsupported_type"]==1
PY

python -m py_compile companyos/runtime/backlog_truth_probe.py
python -m pytest -q tests/test_v34_worker_lease_store.py tests/test_v35_lease_execution_guard.py tests/test_v35_1_dispatcher_ast_contract.py tests/test_v36_live_recovery_qualification.py tests/test_v37_backlog_truth_probe.py
echo "REGRESSION=PASS"

python -m companyos.runtime.backlog_truth_probe | tee "$RT/v37_backlog_before.json"
echo "BACKLOG_PROBE=PASS"

# Validate one and only one supervisor/runtime before throughput work.
SC="$(pgrep -fc 'companyos/runtime/service_supervisor.py' || true)"
CC="$(pgrep -fc 'companyos.runtime.continuous_goal_runtime|companyos/runtime/continuous_goal_runtime.py' || true)"
echo "SUPERVISOR_COUNT=$SC CONTINUOUS_COUNT=$CC"
[ "$SC" -eq 1 ] || { echo "ABORT=supervisor_count"; exit 31; }
[ "$CC" -eq 1 ] || { echo "ABORT=continuous_runtime_count"; exit 32; }

# Observe the existing fenced runtime first; do not add a competing dispatcher.
state_line () {
python - <<'PY'
import json
from companyos.runtime.backlog_truth_probe import probe
x=probe()
print(" ".join(f"{k}={v}" for k,v in sorted(x["states"].items()))+
      " READY="+str(x["reasons"].get("execution_ready",0))+
      " DEP_BLOCKED="+str(x["reasons"].get("dependency_blocked",0))+
      " EXHAUSTED="+str(x["reasons"].get("attempts_exhausted",0)))
PY
}
BASE="$(state_line)"; echo "T+000 $BASE"
for n in 1 2 3 4 5 6; do sleep 10; echo "T+$((n*10)) $(state_line)"; done

python -m companyos.runtime.backlog_truth_probe | tee "$RT/v37_backlog_after.json"

# Inspect recent supervisor errors without mutating queue.
LOG="$RT/supervisor_v36.log"
if [ -f "$LOG" ]; then
  echo "===== RECENT RUNTIME SIGNALS ====="
  tail -400 "$LOG" | grep -Ei 'lease|dispatch|handler|error|exception|traceback|timeout|fail' | tail -80 || true
fi

echo "===== V37 QUALIFICATION ====="
echo "NO_SECOND_DISPATCHER_STARTED=YES"
echo "QUEUE_RECORDS_DELETED=0"
echo "FALSE_COMPLETIONS_CREATED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "SUPERVISOR_RESTARTED=NO"

git add companyos/runtime/backlog_truth_probe.py tests/test_v37_backlog_truth_probe.py
git diff --cached --quiet || git commit -m "V37 add backlog truth classification and bounded drain qualification"
echo "===== V37 COMPLETE ====="
echo "BACKUP=$B"
echo "NEXT=use measured blocker distribution to patch the actual live bottleneck"
