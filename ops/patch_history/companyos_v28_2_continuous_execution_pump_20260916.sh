#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
F="companyos/runtime/continuous_goal_runtime.py"
BACK="$HOME/.companyos_runtime/backups/v28_2_$STAMP"
mkdir -p "$BACK/companyos/runtime"
cp -a "$F" "$BACK/$F"

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/continuous_goal_runtime.py")
s=p.read_text()
if "V28_2_CONTINUOUS_EXECUTION_PUMP" not in s:
    imp="from companyos.runtime.autonomous_ceo_runtime_service import AutonomousCEORuntimeService\n"
    assert imp in s
    s=s.replace(imp,imp+"from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop\n")
    init="        self.ceo_runtime = AutonomousCEORuntimeService(interval_seconds=self.interval_seconds)\n"
    assert init in s
    s=s.replace(init,init+"        self.execution_loop = AutonomousGoalExecutionLoop()\n        self.execution_batch_size = 8\n")
    old="            ceo_state = self.ceo_runtime.startup()\n            self.ceo_runtime.cycle(ceo_state)\n"
    assert old in s
    new="            # V28_2_CONTINUOUS_EXECUTION_PUMP\n            execution_results = self.execution_loop.run_bounded_batch(max_dispatches=self.execution_batch_size)\n            dispatched = sum(1 for r in execution_results if r.dispatched)\n            ceo_state = self.ceo_runtime.load()\n            if not getattr(ceo_state, 'running', False):\n                ceo_state = self.ceo_runtime.startup()\n            self.ceo_runtime.cycle(ceo_state)\n            if dispatched:\n                state.last_reason = f'execution_pump_dispatched:{dispatched}'\n"
    s=s.replace(old,new)
    p.write_text(s)
print("PATCH_APPLIED")
PY

if ! python -m py_compile "$F"; then
  cp -a "$BACK/$F" "$F"
  echo "COMPILE_FAIL_RESTORED"
  exit 1
fi

python - <<'PY'
from pathlib import Path
s=Path("companyos/runtime/continuous_goal_runtime.py").read_text()
assert "V28_2_CONTINUOUS_EXECUTION_PUMP" in s
assert "run_bounded_batch" in s
assert "self.ceo_runtime.load()" in s
print("V28_2_SOURCE_CONTRACT=PASS")
PY

python - <<'PY'
import tempfile
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop
q=AutonomousTaskQueue(Path(tempfile.mkdtemp()))
loop=AutonomousGoalExecutionLoop(q)
q.enqueue(task_type="research",payload={"goal_id":"v282","stage":"research"},priority=100,idempotency_key="v282-r")
q.enqueue(task_type="planning",payload={"goal_id":"v282","stage":"planning","depends_on_stage":"research"},priority=100,idempotency_key="v282-p")
rs=loop.run_bounded_batch(max_dispatches=2)
assert len(rs)==2 and all(r.dispatched for r in rs),rs
print("V28_2_ISOLATED_EXECUTION=PASS")
PY

SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
OLD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
echo "SUPERVISOR_PID=${SUP:-none} OLD_CHILD=${OLD:-none}"
if [ -z "${SUP:-}" ]; then echo "ABORT=no_supervisor"; exit 2; fi
if [ -n "${OLD:-}" ]; then kill "$OLD" 2>/dev/null || true; fi
NEW=""
for i in $(seq 1 30); do
 sleep 1
 C="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
 if [ -n "${C:-}" ] && [ "$C" != "${OLD:-}" ]; then NEW="$C"; break; fi
 echo "waiting=${i}s"
done
if [ -z "$NEW" ]; then cp -a "$BACK/$F" "$F"; echo "ACTIVATION_FAIL_SOURCE_RESTORED"; exit 3; fi
echo "NEW_CHILD=$NEW"
echo "V28_2_ACTIVATION=PASS"

python - <<'PY'
import json,time
from pathlib import Path
from collections import Counter
root=Path.home()/".companyos_runtime"/"task_queue"
def snap():
 c=Counter()
 for p in root.glob("*.json"):
  try:c[str(json.loads(p.read_text()).get("state","UNKNOWN")).upper()]+=1
  except Exception:c["UNREADABLE"]+=1
 return c
a=snap();print("T+000",dict(a),flush=True)
for sec in (15,30,45,60,75):
 time.sleep(15);b=snap()
 print(f"T+{sec:03d}",dict(b),"completed_delta=",b["COMPLETED"]-a["COMPLETED"],"queued_delta=",b["QUEUED"]-a["QUEUED"],"failed_delta=",b["FAILED"]-a["FAILED"],flush=True)
print("FINAL_COMPLETED_DELTA=",b["COMPLETED"]-a["COMPLETED"])
print("FINAL_QUEUED_DELTA=",b["QUEUED"]-a["QUEUED"])
print("FINAL_FAILED_DELTA=",b["FAILED"]-a["FAILED"])
PY

python - <<'PY'
import json
from pathlib import Path
p=Path.home()/".companyos_runtime"/"continuous_goal_runtime_state.json"
if p.exists():
 d=json.loads(p.read_text());print("LAST_REASON=",d.get("last_reason"));print("CYCLES=",d.get("cycles"),"FAILURES=",d.get("consecutive_failures"))
PY

pgrep -af 'companyos.runtime.service_supervisor' || true
pgrep -af 'companyos.runtime.continuous_goal_runtime' || true
echo "V28_2_COMPLETE"
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTARTED=NO"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "BACKUP=$BACK"
