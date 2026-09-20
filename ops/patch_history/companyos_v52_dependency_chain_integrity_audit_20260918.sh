#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V52 READ-ONLY DEPENDENCY CHAIN INTEGRITY AUDIT ====="
python - <<'PY'
import json,time
from collections import Counter,defaultdict
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

q=AutonomousTaskQueue(); tasks=list(q._iter_task_files()); now=time.time()
by_goal_stage=defaultdict(list)
for t in tasks:
    p=t.payload if isinstance(t.payload,dict) else {}
    g=p.get("goal_id"); s=p.get("stage")
    if g and s: by_goal_stage[(str(g),str(s))].append(t)

classes=Counter(); types=defaultdict(Counter); examples=defaultdict(list)
for t in tasks:
    if t.state!="QUEUED": continue
    p=t.payload if isinstance(t.payload,dict) else {}
    dep=p.get("depends_on_stage")
    if not dep: cls="no_dependency"
    elif not p.get("goal_id"): cls="malformed_missing_goal_id"
    else:
        key=(str(p["goal_id"]),str(dep)); prereqs=by_goal_stage.get(key,[])
        states=Counter(x.state for x in prereqs)
        if any(x.state=="COMPLETED" for x in prereqs): cls="dependency_satisfied"
        elif not prereqs: cls="orphan_missing_prerequisite"
        elif any(x.state in ("QUEUED","CLAIMED","RUNNING") for x in prereqs): cls="waiting_on_live_prerequisite"
        elif all(x.state in ("FAILED","CANCELLED") for x in prereqs): cls="blocked_by_terminal_prerequisite"
        else: cls="other_dependency_state"
    classes[cls]+=1; types[t.task_type][cls]+=1
    if len(examples[cls])<8:
        prereq=[]
        if dep and p.get("goal_id"):
            prereq=[{"task_id":x.task_id,"type":x.task_type,"state":x.state,"attempts":x.attempts,
                     "max_attempts":x.max_attempts,"last_error":x.last_error}
                    for x in by_goal_stage.get((str(p["goal_id"]),str(dep)),[])[:4]]
        examples[cls].append({"task_id":t.task_id,"type":t.task_type,"goal_id":p.get("goal_id"),
          "stage":p.get("stage"),"depends_on_stage":dep,"age_sec":round(now-t.created_at_unix,1),
          "prerequisites":prereq})

# goal-chain shapes, useful for spotting duplicated or incomplete research->planning->build chains
shapes=Counter()
for g in {k[0] for k in by_goal_stage}:
    stages=[]
    for (gg,st),xs in by_goal_stage.items():
        if gg==g: stages.append(f"{st}:"+"/".join(sorted(set(x.state for x in xs))))
    shapes[" | ".join(sorted(stages))]+=1

report={"mode":"READ_ONLY","timestamp_unix":now,"total_records":len(tasks),
 "states":dict(Counter(t.state for t in tasks)),
 "queued_dependency_integrity":dict(classes),
 "queued_by_type":{k:dict(v) for k,v in sorted(types.items())},
 "goal_chain_shapes_top20":dict(shapes.most_common(20)),
 "examples":dict(examples)}
out=Path.home()/".companyos_runtime"/f"v52_dependency_chain_integrity_{int(now)}.json"
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,indent=2,sort_keys=True))
print("REPORT=",out)
print("QUEUE_RECORDS_CHANGED=0")
print("V52_DEPENDENCY_AUDIT=PASS")
PY
