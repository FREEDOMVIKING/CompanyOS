#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V50 READ-ONLY DISPATCHABILITY FORENSICS ====="
python - <<'PY'
import json,time
from collections import Counter,defaultdict
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.dependency_aware_dispatcher import DependencyAwareDispatcher

q=AutonomousTaskQueue()
base=AutonomousTaskDispatcher(q)
dep=DependencyAwareDispatcher(base)
now=time.time()
tasks=list(q._iter_task_files())
completed=set()
for t in tasks:
    if t.state=="COMPLETED":
        p=t.payload if isinstance(t.payload,dict) else {}
        if p.get("goal_id") and p.get("stage"):
            completed.add((str(p["goal_id"]),str(p["stage"])))

cats=Counter(); bytype=defaultdict(Counter); examples=defaultdict(list)
for t in tasks:
    if t.state!="QUEUED": continue
    p=t.payload if isinstance(t.payload,dict) else {}
    reason=None
    if t.attempts>=t.max_attempts: reason="attempts_exhausted_while_queued"
    elif t.next_attempt_unix>now: reason="retry_delay"
    elif t.task_type not in base.handlers: reason="no_handler"
    else:
        d=p.get("depends_on_stage")
        if d:
            g=p.get("goal_id")
            if not g: reason="dependency_missing_goal_id"
            elif (str(g),str(d)) not in completed: reason="dependency_blocked"
        if reason is None: reason="READY"
    cats[reason]+=1; bytype[t.task_type][reason]+=1
    if len(examples[reason])<5:
        examples[reason].append({"task_id":t.task_id,"type":t.task_type,"attempts":t.attempts,
          "max_attempts":t.max_attempts,"goal_id":p.get("goal_id"),"stage":p.get("stage"),
          "depends_on_stage":p.get("depends_on_stage"),"age_sec":round(now-t.created_at_unix,1)})

# Reproduce current rotating dispatch window without mutating its cursor.
cursor_path=q.root.parent/"dispatcher_scan_cursor.txt"
try: cursor=int(cursor_path.read_text().strip()) if cursor_path.exists() else 0
except: cursor=0
scan_limit=max(64*16,1000)
window=q.bounded_candidates_window(scan_limit,cursor)
wc=Counter()
for t in window:
    if t.state!="QUEUED": continue
    p=t.payload if isinstance(t.payload,dict) else {}
    if t.attempts>=t.max_attempts: r="attempts_exhausted_while_queued"
    elif t.next_attempt_unix>now:r="retry_delay"
    elif t.task_type not in base.handlers:r="no_handler"
    elif p.get("depends_on_stage") and (not p.get("goal_id") or (str(p.get("goal_id")),str(p.get("depends_on_stage"))) not in completed):r="dependency_blocked"
    else:r="READY"
    wc[r]+=1

report={"mode":"READ_ONLY","timestamp_unix":now,"total_records":len(tasks),
 "states":dict(Counter(t.state for t in tasks)),"handlers":sorted(base.handlers),
 "completed_goal_stages":len(completed),"queued_classification":dict(cats),
 "queued_by_type":{k:dict(v) for k,v in sorted(bytype.items())},
 "current_cursor":cursor,"scan_limit":scan_limit,"window_records":len(window),
 "window_queued_classification":dict(wc),"examples":dict(examples)}
out=Path.home()/".companyos_runtime"/f"v50_dispatchability_forensics_{int(now)}.json"
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,indent=2,sort_keys=True))
print("REPORT=",out)
print("QUEUE_RECORDS_CHANGED=0")
print("V50_FORENSICS=PASS")
PY
