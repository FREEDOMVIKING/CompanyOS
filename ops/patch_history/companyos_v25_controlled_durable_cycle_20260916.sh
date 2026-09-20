#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
PY="${PYTHON:-python}"
R="$HOME/.companyos_runtime"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="$R/v25_controlled_cycle_$STAMP.log"
mkdir -p "$R"

echo "===== COMPANYOS V25 CONTROLLED DURABLE CYCLE ====="
echo "Supervisor restart: NO"
echo "External/finance actions: NOT enabled by this script"
echo "Log: $LOG"

echo "===== PRECHECK ====="
"$PY" -m py_compile \
  companyos/runtime/autonomous_task_queue.py \
  companyos/runtime/dependency_aware_dispatcher.py \
  companyos/runtime/durable_execution_closure.py
echo "COMPILE=PASS"

"$PY" - <<'PY'
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue()
print("READABLE_TASKS_BEFORE=",sum(1 for _ in q._iter_task_files()))
PY

echo "===== BOUNDED ONE-CYCLE EXECUTION ====="
set +e
timeout --signal=INT --kill-after=5s 45s \
  "$PY" - <<'PY' 2>&1 | tee "$LOG"
import json, time, traceback
from pathlib import Path
from companyos.runtime.durable_execution_closure import DurableExecutionClosure

print("V25_CYCLE_START=", time.time(), flush=True)
runner = DurableExecutionClosure()

try:
    if hasattr(runner, "cycle"):
        result = runner.cycle()
    elif hasattr(runner, "run_once"):
        result = runner.run_once()
    elif hasattr(runner, "run"):
        # Only use run if signature/default behavior is one-shot.
        import inspect
        sig = inspect.signature(runner.run)
        if len(sig.parameters) == 0:
            result = runner.run()
        else:
            raise RuntimeError("No safe one-cycle entrypoint found")
    else:
        raise RuntimeError("No supported durable execution entrypoint found")
    print("V25_RESULT_BEGIN", flush=True)
    try:
        print(json.dumps(result, indent=2, default=str), flush=True)
    except Exception:
        print(repr(result), flush=True)
    print("V25_RESULT_END", flush=True)
    print("V25_ONE_CYCLE=PASS", flush=True)
except KeyboardInterrupt:
    print("V25_ONE_CYCLE=INTERRUPTED", flush=True)
    raise
except Exception as e:
    print("V25_ONE_CYCLE=ERROR", type(e).__name__, str(e), flush=True)
    traceback.print_exc()
    raise
PY
RC=${PIPESTATUS[0]}
set -e

echo "V25_PROCESS_RC=$RC"
if [ "$RC" -eq 124 ] || [ "$RC" -eq 137 ]; then
  echo "V25_TIMEOUT=YES"
elif [ "$RC" -eq 130 ]; then
  echo "V25_INTERRUPTED_AT_TIMEOUT=YES"
else
  echo "V25_TIMEOUT=NO"
fi

echo "===== POST-CYCLE QUEUE HEALTH ====="
"$PY" - <<'PY'
from pathlib import Path
import json
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

q=AutonomousTaskQueue()
readable=sum(1 for _ in q._iter_task_files())
bad=[]
root=Path.home()/".companyos_runtime"/"task_queue"
for p in root.glob("*.json"):
    try:
        json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        bad.append((p.name,type(e).__name__))

print("READABLE_TASKS_AFTER=",readable)
print("MALFORMED_AFTER=",len(bad))
for x in bad[:10]:
    print("BAD_RECORD=",x)
if bad:
    raise SystemExit("QUEUE_HEALTH=FAIL")
print("QUEUE_HEALTH=PASS")
PY

echo "===== RECENT TASK MUTATIONS ====="
find "$R/task_queue" -maxdepth 1 -type f -name '*.json' \
  -mmin -3 -printf '%TY-%Tm-%Td %TH:%TM:%TS %p\n' 2>/dev/null \
  | sort -r | head -20 || true

echo "===== SUPERVISOR PRESERVATION ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
echo "HEALTHY_SUPERVISOR_RESTARTED=NO"

echo "===== V25 SUMMARY ====="
if grep -q 'V25_ONE_CYCLE=PASS' "$LOG" && [ "$RC" -eq 0 ]; then
  echo "COMPANYOS_V25_CONTROLLED_CYCLE=PASS"
else
  echo "COMPANYOS_V25_CONTROLLED_CYCLE=NEEDS_INSPECTION"
  echo "This is bounded; CompanyOS supervisor was not restarted."
fi
echo "LOG_FILE=$LOG"
exit 0
