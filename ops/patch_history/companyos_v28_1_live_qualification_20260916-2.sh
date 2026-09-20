#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"

echo "===== COMPANYOS V28.1 LIVE EXECUTION QUALIFICATION ====="

SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
OLD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
echo "SUPERVISOR_PID=${SUP:-none}"
echo "OLD_CONTINUOUS_PID=${OLD:-none}"
[ -n "${SUP:-}" ] || { echo "ABORT=no_supervisor"; exit 2; }

echo "===== SOURCE CONTRACT ====="
python - <<'PY'
from pathlib import Path
q=Path("companyos/runtime/autonomous_task_queue.py").read_text()
d=Path("companyos/runtime/autonomous_task_dispatcher.py").read_text()
x=Path("companyos/runtime/dependency_aware_dispatcher.py").read_text()
assert 'sorted(self.root.glob("*.json")' in q
assert "def dispatch_task(" in d
assert "next_attempt_unix<=now" in d.replace(" ","")
assert "10**9" not in x
assert "dispatch_task(c[0])" in x
print("V28_SOURCE_CONTRACT=PASS")
PY

echo "===== READ-ONLY QUEUE BASELINE ====="
python - <<'PY'
import json,time
from pathlib import Path
from collections import Counter
root=Path.home()/".companyos_runtime"/"task_queue"
c=Counter(); ready=Counter()
for p in root.glob("*.json"):
    try:x=json.loads(p.read_text())
    except Exception:c["UNREADABLE"]+=1;continue
    st=str(x.get("state","UNKNOWN")).upper(); c[st]+=1
    if st=="QUEUED" and int(x.get("attempts",0))<int(x.get("max_attempts",3)) and float(x.get("next_attempt_unix",0))<=time.time():
        ready[str(x.get("task_type","UNKNOWN"))]+=1
print("STATES=",dict(c))
print("RETRY_DUE_BY_TYPE=",dict(ready))
PY

echo "===== CONTROLLED CHILD RELOAD ====="
if [ -n "${OLD:-}" ]; then kill "$OLD" 2>/dev/null || true; fi
NEW=""
for i in $(seq 1 30); do
  sleep 1
  C="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
  if [ -n "${C:-}" ] && [ "$C" != "${OLD:-}" ]; then NEW="$C"; break; fi
  echo "waiting=${i}s"
done
[ -n "${NEW:-}" ] || { echo "QUALIFICATION_FAIL=child_not_respawned"; exit 3; }
echo "NEW_CONTINUOUS_PID=$NEW"
echo "CHILD_RELOAD=PASS"

echo "===== EXACT IN-PROCESS CONTRACT ====="
python - <<'PY'
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop
x=AutonomousGoalExecutionLoop()
base=x.dispatcher.dispatcher
print("HANDLERS=",sorted(base.handlers))
assert {"research","planning","build"}.issubset(base.handlers)
assert hasattr(base,"dispatch_task")
print("LIVE_CLASS_CONTRACT=PASS")
PY

echo "===== 90 SECOND THROUGHPUT ====="
python - <<'PY'
import json,time
from pathlib import Path
from collections import Counter
root=Path.home()/".companyos_runtime"/"task_queue"
def snap():
 c=Counter()
 for p in root.glob("*.json"):
  try:x=json.loads(p.read_text());c[str(x.get("state","UNKNOWN")).upper()]+=1
  except Exception:c["UNREADABLE"]+=1
 return c
a=snap(); print("T+000",dict(a),flush=True)
for sec in (15,30,45,60,75,90):
 time.sleep(15); b=snap()
 print(f"T+{sec:03d}",dict(b),
       "completed_delta=",b["COMPLETED"]-a["COMPLETED"],
       "queued_delta=",b["QUEUED"]-a["QUEUED"],
       "failed_delta=",b["FAILED"]-a["FAILED"],flush=True)
print("FINAL_COMPLETED_DELTA=",b["COMPLETED"]-a["COMPLETED"])
print("FINAL_QUEUED_DELTA=",b["QUEUED"]-a["QUEUED"])
print("FINAL_FAILED_DELTA=",b["FAILED"]-a["FAILED"])
PY

echo "===== ONE SAFE INTERNAL PROBE IF STILL STALLED ====="
python - <<'PY'
import json,time
from pathlib import Path
from collections import Counter
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop
root=Path.home()/".companyos_runtime"/"task_queue"
def count_completed():
 n=0
 for p in root.glob("*.json"):
  try:
   if str(json.loads(p.read_text()).get("state","")).upper()=="COMPLETED":n+=1
  except Exception:pass
 return n
before=count_completed()
loop=AutonomousGoalExecutionLoop()
r=loop.cycle()
after=count_completed()
print("PROBE_DISPATCHED=",r.dispatched)
print("PROBE_TASK_ID=",r.task_id)
print("PROBE_STATE=",r.state)
print("PROBE_REASON=",r.reason)
print("PROBE_COMPLETED_DELTA=",after-before)
PY

echo "===== RECENT TASK ERRORS ====="
python - <<'PY'
import json
from pathlib import Path
rows=[]
for p in (Path.home()/".companyos_runtime"/"task_queue").glob("*.json"):
 try:x=json.loads(p.read_text())
 except Exception:continue
 if x.get("last_error"):
  rows.append((float(x.get("updated_at_unix",0)),p.name,x))
for _,name,x in sorted(rows,reverse=True)[:10]:
 print(name,x.get("state"),x.get("task_type"),str(x.get("last_error"))[:300])
PY

echo "===== PROCESS HEALTH ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
pgrep -af 'companyos.runtime.continuous_goal_runtime' || true
echo "V28_1_QUALIFICATION_COMPLETE"
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTARTED=NO"
echo "FINANCE_CONNECTORS_CHANGED=NO"
