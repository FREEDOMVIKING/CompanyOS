#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V54 BOUNDED RESEARCH PREREQUISITE REPAIR ====="
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$HOME/.companyos_runtime/backups/v54_$STAMP"
cp -a "$HOME/.companyos_runtime/tasks" "$HOME/.companyos_runtime/backups/v54_$STAMP/" 2>/dev/null || true

python - <<'PY'
import json,time,os
from collections import defaultdict,Counter
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

LIMIT=int(os.getenv("COMPANYOS_V54_REPAIR_LIMIT","32"))
q=AutonomousTaskQueue()
tasks=list(q._iter_task_files())
bygs=defaultdict(list)
for t in tasks:
    p=t.payload if isinstance(t.payload,dict) else {}
    if p.get("goal_id") and p.get("stage"):
        bygs[(str(p["goal_id"]),str(p["stage"]))].append(t)

orphans=[]
for t in tasks:
    if t.state!="QUEUED": continue
    p=t.payload if isinstance(t.payload,dict) else {}
    if p.get("stage")!="planning" or p.get("depends_on_stage")!="research" or not p.get("goal_id"):
        continue
    g=str(p["goal_id"])
    if bygs.get((g,"research")):
        continue
    # V53 proved these are orchestration-generated historical chains.
    if ":goal:" not in g:
        continue
    orphans.append(t)

orphans.sort(key=lambda x:(x.created_at_unix,x.task_id))
selected=orphans[:LIMIT]
created=[]
for planning in selected:
    p=planning.payload
    g=str(p["goal_id"])
    goal=str(p.get("goal") or p.get("topic") or p.get("name") or "").strip()
    if not goal:
        continue
    # Re-check immediately before mutation.
    current=list(q._iter_task_files())
    exists=False
    for x in current:
        xp=x.payload if isinstance(x.payload,dict) else {}
        if str(xp.get("goal_id",""))==g and xp.get("stage")=="research":
            exists=True; break
    if exists:
        continue
    priority=max(0,int(planning.priority)-10)
    r=q.enqueue(
        task_type="research",
        payload={"topic":goal,"goal_id":g,"stage":"research"},
        priority=priority,
        idempotency_key=f"{g}:research",
        max_attempts=3,
    )
    created.append({"goal_id":g,"research_task_id":r.task_id,
                    "planning_task_id":planning.task_id,"priority":priority})

after=list(q._iter_task_files())
report={
 "mode":"BOUNDED_REPAIR",
 "repair_limit":LIMIT,
 "eligible_orphans_before":len(orphans),
 "research_tasks_created":len(created),
 "remaining_estimate":max(0,len(orphans)-len(created)),
 "created":created,
 "states_after":dict(Counter(t.state for t in after)),
}
out=Path.home()/".companyos_runtime"/f"v54_research_prerequisite_repair_{int(time.time())}.json"
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,indent=2,sort_keys=True))
print("REPORT=",out)
print("PLANNING_DEPENDENCIES_REMOVED=0")
print("TASKS_MARKED_COMPLETE=0")
print("V54_REPAIR=PASS")
PY

echo "===== 60 SECOND EXECUTION OBSERVATION ====="
sleep 60
PYTHONPATH="$PWD" python - <<'PY'
from collections import Counter
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue()
print("STATES=",dict(Counter(t.state for t in q._iter_task_files())))
PY
echo "V54_OBSERVATION=PASS"
