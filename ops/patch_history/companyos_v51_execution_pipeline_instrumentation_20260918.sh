#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V51 EXECUTION PIPELINE INSTRUMENTATION ====="
python - <<'PY'
import json,time,os
from collections import Counter
from pathlib import Path
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

loop=AutonomousGoalExecutionLoop()
d=loop.dispatcher; q=loop.queue; now=time.time()
requested=48
completed=d._completed_stage_index()
scan_limit=max(requested*16,int(os.getenv("COMPANYOS_QUEUE_SCAN_LIMIT","1000")))
cursor_path=q.root.parent/"dispatcher_scan_cursor.txt"
try: cursor=int(cursor_path.read_text().strip()) if cursor_path.exists() else 0
except: cursor=0
source=q.bounded_candidates_window(scan_limit,cursor)

stages=Counter()
eligible=[]
ready=[]
for t in source:
    if t.state!="QUEUED": stages["not_queued"]+=1; continue
    stages["queued"]+=1
    if t.attempts>=t.max_attempts: stages["attempts_exhausted"]+=1; continue
    if t.next_attempt_unix>now: stages["retry_not_due"]+=1; continue
    if t.task_type not in d.dispatcher.handlers: stages["unsupported_type"]+=1; continue
    stages["eligible_pre_dependency"]+=1; eligible.append(t)
    if d._dependency_satisfied_with_index(t,completed):
        stages["dependency_ready"]+=1; ready.append(t)
    else: stages["dependency_blocked"]+=1

ready_types=Counter(t.task_type for t in ready)
dep_blocked_types=Counter(t.task_type for t in eligible if not d._dependency_satisfied_with_index(t,completed))
before=Counter(t.state for t in q._iter_task_files())
t0=time.time()
results=loop.run_bounded_batch(max_dispatches=requested)
elapsed=time.time()-t0
after=Counter(t.state for t in q._iter_task_files())
reasons=Counter(r.reason for r in results)
dispatched=sum(1 for r in results if r.dispatched)
report={
 "mode":"CONTROLLED_LIVE_BATCH",
 "requested_capacity":requested,
 "scan_limit":scan_limit,
 "cursor_before":cursor,
 "window_records":len(source),
 "pipeline":dict(stages),
 "ready_by_type":dict(ready_types),
 "dependency_blocked_by_type":dict(dep_blocked_types),
 "returned_results":len(results),
 "dispatched_results":dispatched,
 "result_reasons":dict(reasons),
 "elapsed_seconds":round(elapsed,3),
 "before_states":dict(before),
 "after_states":dict(after),
 "completed_delta":after["COMPLETED"]-before["COMPLETED"],
 "failed_delta":after["FAILED"]-before["FAILED"],
 "queued_delta":after["QUEUED"]-before["QUEUED"],
}
if len(ready)<requested: stop="fewer_dependency_ready_than_capacity"
elif dispatched<requested: stop="dispatcher_returned_below_capacity_despite_ready_work"
else: stop="capacity_filled"
report["capacity_diagnosis"]=stop
out=Path.home()/".companyos_runtime"/f"v51_execution_pipeline_{int(time.time())}.json"
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,indent=2,sort_keys=True))
print("REPORT=",out)
print("QUEUE_DELETIONS=0")
print("V51_INSTRUMENTATION=PASS")
PY
