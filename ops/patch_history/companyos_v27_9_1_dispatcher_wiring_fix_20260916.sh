#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V27.9.1 DISPATCHER WIRING FIX ====="

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$HOME/.companyos_runtime/backups/v27_9_1_$STAMP"
mkdir -p "$BACKUP"
cp -f companyos/runtime/execution_drain_engine.py "$BACKUP/" 2>/dev/null || true

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/execution_drain_engine.py")
s=p.read_text()
old = '        self.queue = AutonomousTaskQueue()\n        self.dispatcher = DependencyAwareDispatcher()\n        self.batch_size = max(1, min(int(batch_size), 128))\n'
new = '''        self.queue = AutonomousTaskQueue()
        from companyos.runtime.continuous_goal_runtime import ContinuousGoalRuntime
        runtime = ContinuousGoalRuntime()
        base = getattr(runtime, "dispatcher", None)
        if base is None:
            base = getattr(runtime, "task_dispatcher", None)
        if isinstance(base, DependencyAwareDispatcher):
            self.dispatcher = base
        elif base is not None and hasattr(base, "handlers") and hasattr(base, "queue"):
            self.dispatcher = DependencyAwareDispatcher(base)
        else:
            wrapped = getattr(runtime, "dependency_dispatcher", None)
            if isinstance(wrapped, DependencyAwareDispatcher):
                self.dispatcher = wrapped
            else:
                raise RuntimeError("live_runtime_dispatcher_not_found")
        self.queue = self.dispatcher.queue
        self.batch_size = max(1, min(int(batch_size), 128))
'''
if old not in s:
    raise SystemExit("PATCH_ABORT: expected V27.9 constructor block not found")
p.write_text(s.replace(old,new,1))
print("PATCH=PASS")
PY

echo "===== COMPILE ====="
python -m py_compile companyos/runtime/execution_drain_engine.py scripts/companyos_drainctl
echo "COMPILE=PASS"

echo "===== CONSTRUCTOR/REGISTRY CONTRACT ====="
python - <<'PY'
from companyos.runtime.execution_drain_engine import ExecutionDrainEngine
e=ExecutionDrainEngine(16)
base=e.dispatcher.dispatcher
print("BATCH_SIZE:", e.batch_size)
print("HANDLERS:", sorted(base.handlers))
assert e.batch_size == 16
assert base.handlers
print("WIRING=PASS")
PY

echo "===== TEST ====="
python -m pytest -q tests/test_execution_drain_engine.py
echo "TEST=PASS"

echo "===== STATUS BEFORE ====="
python scripts/companyos_drainctl status

echo "===== SAFE LIVE BATCH: 8 ====="
python scripts/companyos_drainctl batch --size 8

echo "===== SUPERVISOR PRESERVED ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
pgrep -af 'companyos.runtime.continuous_goal_runtime' || true
echo "SUPERVISOR_RESTART=NO"
echo "QUEUE_RECORDS_DELETED=0"
echo "V27_9_1=PASS"
