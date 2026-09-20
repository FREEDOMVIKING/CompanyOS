#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$HOME/.companyos_runtime/backups/v27_7_$STAMP"
mkdir -p "$BACKUP"

echo "===== COMPANYOS V27.7 LIVE SPECIALIST EXECUTION ====="
for f in companyos/runtime/autonomous_goal_execution_loop.py companyos/runtime/autonomous_ceo_orchestrator.py; do
  [ -f "$f" ] && cp --parents "$f" "$BACKUP/"
done

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/autonomous_goal_execution_loop.py")
s=p.read_text()
old='''        base_dispatcher = AutonomousTaskDispatcher(self.queue)
        register_default_specialists(base_dispatcher)
        self.dispatcher = DependencyAwareDispatcher(base_dispatcher)
'''
new='''        base_dispatcher = AutonomousTaskDispatcher(self.queue)
        register_default_specialists(base_dispatcher)
        required = {"research", "planning", "build"}
        missing = sorted(required.difference(base_dispatcher.handlers))
        if missing:
            raise RuntimeError("missing_default_specialist_handlers:" + ",".join(missing))
        self.dispatcher = DependencyAwareDispatcher(base_dispatcher)
'''
if old in s:
    s=s.replace(old,new,1)
elif "missing_default_specialist_handlers" not in s:
    raise SystemExit("V27_7_ABORT: execution-loop constructor changed")

if "def run_bounded_batch(" not in s:
    marker="    def run_until_idle(\n"
    addition='''    def run_bounded_batch(self, *, max_dispatches: int = 8):
        # Bounded internal throughput; existing queue/dependency gates remain authoritative.
        results = []
        for _ in range(max(1, min(int(max_dispatches), 64))):
            result = self.cycle()
            results.append(result)
            if not result.dispatched:
                break
        return results

'''
    if marker not in s:
        raise SystemExit("V27_7_ABORT: run_until_idle marker missing")
    s=s.replace(marker,addition+marker,1)
p.write_text(s)
PY

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/autonomous_ceo_orchestrator.py")
s=p.read_text()
old='''        # First advance at most one dependency-ready task.
        dispatch = self.execution_loop.cycle()
'''
new='''        # Advance a bounded batch of dependency-ready internal tasks.
        import os
        batch_size = max(1, min(int(os.getenv("COMPANYOS_TASKS_PER_CEO_CYCLE", "8")), 64))
        batch = self.execution_loop.run_bounded_batch(max_dispatches=batch_size)
        dispatch = batch[-1]
        for item in reversed(batch):
            if item.dispatched:
                dispatch = item
                break
'''
if old in s:
    s=s.replace(old,new,1)
elif "COMPANYOS_TASKS_PER_CEO_CYCLE" not in s:
    raise SystemExit("V27_7_ABORT: CEO dispatch source changed")
p.write_text(s)
PY

python -m py_compile companyos/runtime/autonomous_goal_execution_loop.py companyos/runtime/autonomous_ceo_orchestrator.py companyos/runtime/default_specialist_registry.py companyos/runtime/dependency_aware_dispatcher.py
echo "COMPILE=PASS"

python - <<'PY'
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.default_specialist_registry import register_default_specialists
q=AutonomousTaskQueue(); d=AutonomousTaskDispatcher(q); register_default_specialists(d)
required={"research","planning","build"}
print("REGISTERED_HANDLERS=",sorted(d.handlers))
missing=required-set(d.handlers)
print("MISSING_HANDLERS=",sorted(missing))
if missing: raise SystemExit("REGISTRY_CONTRACT=FAIL")
print("REGISTRY_CONTRACT=PASS")
PY

ENV="$HOME/.companyos_launch_env"
touch "$ENV"
grep -q '^COMPANYOS_QUEUE_SCAN_LIMIT=' "$ENV" || echo 'export COMPANYOS_QUEUE_SCAN_LIMIT=2000' >> "$ENV"
grep -q '^COMPANYOS_TASKS_PER_CEO_CYCLE=' "$ENV" || echo 'export COMPANYOS_TASKS_PER_CEO_CYCLE=8' >> "$ENV"
chmod 600 "$ENV"

echo "===== LIVE LOOP ====="
python - <<'PY'
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop
loop=AutonomousGoalExecutionLoop()
print("LIVE_HANDLERS=",sorted(loop.dispatcher.dispatcher.handlers))
print("LIVE_LOOP_CONSTRUCTION=PASS")
PY

echo "===== QUEUE BEFORE ====="
python - <<'PY'
from collections import Counter
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
print(dict(Counter(t.state for t in AutonomousTaskQueue().all_tasks())))
PY

# Preserve supervisor; reload only its continuous-goal child.
OLDPID="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
echo "CONTINUOUS_OLD_PID=${OLDPID:-none}"
if [ -n "${OLDPID:-}" ]; then kill "$OLDPID" 2>/dev/null || true; sleep 8; fi

echo "===== PROCESSES ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
pgrep -af 'companyos.runtime.continuous_goal_runtime' || true

source "$ENV"
echo "===== 30 SECOND MOVEMENT TEST ====="
python - <<'PY'
import time
from collections import Counter
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
def c(): return Counter(t.state for t in AutonomousTaskQueue().all_tasks())
a=c(); print("BEFORE_WAIT=",dict(a)); time.sleep(30); b=c()
print("AFTER_WAIT=",dict(b))
print("COMPLETED_DELTA=",b.get("COMPLETED",0)-a.get("COMPLETED",0))
print("QUEUED_DELTA=",b.get("QUEUED",0)-a.get("QUEUED",0))
PY

git add companyos/runtime/autonomous_goal_execution_loop.py companyos/runtime/autonomous_ceo_orchestrator.py
if ! git diff --cached --quiet; then
  git commit -m "V27.7 restore live specialist execution throughput"
  git push origin "$(git branch --show-current)"
else
  echo "V27.7: no new tracked diff"
fi

echo "===== V27.7 COMPLETE ====="
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_INTENTIONAL_RESTART=NO"
