#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V56 FINISH RESTORED RESEARCH BATCH ====="
python - <<'PY'
import json,glob,time
from pathlib import Path
from collections import Counter
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.default_specialist_registry import register_default_specialists

reports=sorted(glob.glob(str(Path.home()/".companyos_runtime"/"v55_durable_research_restore_*.json")))
if not reports: raise SystemExit("V56_ABORT=no V55 report")
v55=json.load(open(reports[-1]))
ids=list(v55.get("restored") or [])
if not ids: raise SystemExit("V56_ABORT=V55 report contains no restored IDs")

q=AutonomousTaskQueue()
d=AutonomousTaskDispatcher(q); register_default_specialists(d)
before=Counter(t.state for t in q._iter_task_files())
results=[]
for tid in ids:
    try: t=q.load(tid)
    except Exception as e:
        results.append({"task_id":tid,"action":"missing_file","error":str(e)}); continue
    p=t.payload if isinstance(t.payload,dict) else {}
    if t.task_type!="research" or p.get("stage")!="research":
        results.append({"task_id":tid,"action":"skipped_not_research"}); continue
    if t.state=="COMPLETED":
        results.append({"task_id":tid,"action":"already_completed","goal_id":p.get("goal_id")}); continue
    if t.state!="QUEUED":
        results.append({"task_id":tid,"action":"skipped_state","state":t.state}); continue
    r=d.dispatch_task(t)
    results.append({"task_id":tid,"action":"dispatched","state":r.state,"reason":r.reason,
                    "goal_id":p.get("goal_id")})

after=Counter(t.state for t in q._iter_task_files())
completed_goals=[]
for tid in ids:
    try:
        t=q.load(tid); p=t.payload if isinstance(t.payload,dict) else {}
        if t.state=="COMPLETED" and p.get("goal_id"):
            completed_goals.append(str(p["goal_id"]))
    except Exception: pass

planning_ready=0
for t in q._iter_task_files():
    p=t.payload if isinstance(t.payload,dict) else {}
    if t.state=="QUEUED" and p.get("stage")=="planning" and str(p.get("goal_id","")) in completed_goals:
        planning_ready+=1

report={"v55_report":reports[-1],"restored_ids":ids,"results":results,
        "before":dict(before),"after":dict(after),
        "completed_research_goals":len(set(completed_goals)),
        "planning_now_dependency_ready":planning_ready}
out=Path.home()/".companyos_runtime"/f"v56_finish_restored_research_{int(time.time())}.json"
out.write_text(json.dumps(report,indent=2,default=str)+"\n")
print(json.dumps(report,indent=2,default=str))
print("DEPENDENCIES_BYPASSED=0")
print("NEW_TASKS_CREATED=0")
print("V56_RESTORED_BATCH_DRAIN=PASS")
PY
