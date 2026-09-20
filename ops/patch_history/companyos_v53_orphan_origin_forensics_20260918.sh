#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V53 READ-ONLY ORPHAN ORIGIN FORENSICS ====="
python - <<'PY'
import json,time
from collections import Counter,defaultdict
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue(); tasks=list(q._iter_task_files())
bygs=defaultdict(list); bykey=defaultdict(list)
for t in tasks:
 p=t.payload if isinstance(t.payload,dict) else {}
 if p.get("goal_id") and p.get("stage"): bygs[(str(p["goal_id"]),str(p["stage"]))].append(t)
 if t.idempotency_key: bykey[t.idempotency_key].append(t)
orph=[]
for t in tasks:
 if t.state!="QUEUED": continue
 p=t.payload if isinstance(t.payload,dict) else {}
 if p.get("stage")=="planning" and p.get("depends_on_stage")=="research" and p.get("goal_id"):
  g=str(p["goal_id"])
  if not bygs.get((g,"research")):
   orph.append(t)
patterns=Counter(); evidence=Counter(); samples=[]
for t in orph:
 p=t.payload; g=str(p["goal_id"]); expected=f"{g}:research"
 keyrows=bykey.get(expected,[])
 if keyrows: ev="research_key_exists_but_goal_stage_mismatch"
 else: ev="research_task_absent"
 evidence[ev]+=1
 if ":goal:" in g: pat="orchestration_goal_id"
 elif g.count(":")>=2: pat="colon_structured_goal_id"
 else: pat="uuid_or_other_goal_id"
 patterns[pat]+=1
 if len(samples)<20:
  siblings=[]
  for stage in ("research","planning","build"):
   for x in bygs.get((g,stage),[])[:3]:
    siblings.append({"stage":stage,"task_id":x.task_id,"state":x.state,"key":x.idempotency_key})
  samples.append({"planning_task_id":t.task_id,"goal_id":g,"planning_key":t.idempotency_key,
   "expected_research_key":expected,"origin_evidence":ev,"siblings":siblings,
   "goal_text":p.get("goal")})
# Current decomposer contract check from source text.
src=Path("companyos/runtime/ceo_goal_decomposer.py").read_text()
contract={"creates_research":'"task_type": "research"' in src,
 "creates_planning":'"task_type": "planning"' in src,
 "creates_build":'"task_type": "build"' in src,
 "planning_depends_research":'"depends_on_stage": "research"' in src,
 "research_key_contract":'f"{goal_id}:research"' in src}
report={"mode":"READ_ONLY","orphan_planning_count":len(orph),"origin_evidence":dict(evidence),
 "goal_id_patterns":dict(patterns),"current_decomposer_contract":contract,
 "samples":samples,"total_records":len(tasks),"states":dict(Counter(t.state for t in tasks))}
out=Path.home()/".companyos_runtime"/f"v53_orphan_origin_{int(time.time())}.json"
out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
print(json.dumps(report,indent=2,sort_keys=True))
print("REPORT=",out); print("QUEUE_RECORDS_CHANGED=0"); print("V53_ORIGIN_FORENSICS=PASS")
PY
