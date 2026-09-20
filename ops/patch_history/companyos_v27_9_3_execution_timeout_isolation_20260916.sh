#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "${HOME}/companyos"

echo "===== COMPANYOS V27.9.3 EXECUTION TIMEOUT ISOLATION ====="
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="${HOME}/.companyos_runtime/backups/v27_9_3_${TS}"
mkdir -p "$BACKUP" companyos/runtime tests

for f in companyos/runtime/execution_drain_engine.py companyos/runtime/autonomous_task_dispatcher.py; do
  [ -f "$f" ] && cp -a "$f" "$BACKUP/"
done
echo "BACKUP=$BACKUP"

cat > companyos/runtime/bounded_task_execution.py <<'PY'
from __future__ import annotations
import concurrent.futures
import os
import time
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class BoundedExecutionResult:
    ok: bool
    value: Any = None
    error: str | None = None
    timed_out: bool = False
    elapsed_seconds: float = 0.0

def run_bounded(fn: Callable[[], Any], timeout_seconds: float | None = None) -> BoundedExecutionResult:
    timeout = float(timeout_seconds or os.getenv("COMPANYOS_TASK_TIMEOUT_SECONDS", "90"))
    started = time.monotonic()
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="companyos-task")
    fut = pool.submit(fn)
    try:
        value = fut.result(timeout=timeout)
        return BoundedExecutionResult(True, value=value, elapsed_seconds=time.monotonic()-started)
    except concurrent.futures.TimeoutError:
        fut.cancel()
        # Do not wait for a stuck worker during shutdown.
        pool.shutdown(wait=False, cancel_futures=True)
        return BoundedExecutionResult(False, error=f"task_timeout_after_{timeout:g}s",
                                      timed_out=True, elapsed_seconds=time.monotonic()-started)
    except Exception as exc:
        return BoundedExecutionResult(False, error=f"{type(exc).__name__}: {exc}",
                                      elapsed_seconds=time.monotonic()-started)
    finally:
        if fut.done():
            pool.shutdown(wait=False, cancel_futures=True)
PY

cat > tests/test_bounded_task_execution.py <<'PY'
import time
from companyos.runtime.bounded_task_execution import run_bounded

def test_success():
    r=run_bounded(lambda: 7, .2)
    assert r.ok and r.value == 7 and not r.timed_out

def test_timeout_is_bounded():
    start=time.monotonic()
    r=run_bounded(lambda: time.sleep(1), .05)
    assert not r.ok and r.timed_out
    assert time.monotonic()-start < .5

def test_exception_is_captured():
    def boom():
        raise ValueError("x")
    r=run_bounded(boom, .2)
    assert not r.ok and "ValueError" in (r.error or "")
PY

python -m py_compile companyos/runtime/bounded_task_execution.py
python -m pytest -q tests/test_bounded_task_execution.py

echo "===== QUEUE HEALTH ====="
python - <<'PY'
import json
from collections import Counter
from pathlib import Path
root=Path.home()/".companyos_runtime"/"task_queue"
c=Counter()
bad=0
for p in root.glob("*.json"):
    try:
        x=json.loads(p.read_text())
        c[str(x.get("state","UNKNOWN")).upper()] += 1
    except Exception:
        bad += 1
print("STATES=",dict(c))
print("UNREADABLE=",bad)
PY

echo "===== INSTALL EXECUTION-DRAIN SAFETY WRAPPER ====="
python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/execution_drain_engine.py")
if not p.exists():
    print("DRAIN_ENGINE_NOT_PRESENT_SKIP_PATCH")
    raise SystemExit(0)

s=p.read_text()
if "V27_9_3_BOUNDED_EXECUTION" in s:
    print("ALREADY_PATCHED")
    raise SystemExit(0)

# Conservative patch: add helper import only. Existing dispatcher behavior is not rewritten blindly.
needle="from __future__ import annotations"
addition="\n# V27_9_3_BOUNDED_EXECUTION\nfrom companyos.runtime.bounded_task_execution import run_bounded\n"
if needle in s:
    pos=s.find("\n", s.find(needle))
    s=s[:pos+1]+addition+s[pos+1:]
else:
    s=addition+s
p.write_text(s)
print("SAFE_HELPER_IMPORTED")
PY

python -m py_compile companyos/runtime/execution_drain_engine.py 2>/dev/null || {
  echo "COMPILE_FAILED_RESTORING"
  cp "$BACKUP/execution_drain_engine.py" companyos/runtime/execution_drain_engine.py
  exit 1
}

echo "===== SUPERVISOR PRESERVATION ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
pgrep -af 'companyos.runtime.continuous_goal_runtime' || true

echo "===== GIT CHECKPOINT (EXPLICIT FILES ONLY) ====="
git add companyos/runtime/bounded_task_execution.py tests/test_bounded_task_execution.py
git add companyos/runtime/execution_drain_engine.py 2>/dev/null || true
if ! git diff --cached --quiet; then
  git commit -m "V27.9.3 add bounded execution timeout isolation" || true
fi

echo "===== V27.9.3 PASS ====="
echo "TASK_TIMEOUT_DEFAULT=90s"
echo "NO_QUEUE_RECORDS_DELETED"
echo "NO_FINANCE_CONNECTORS_CHANGED"
echo "NO_SUPERVISOR_RESTART"
echo "NEXT=wire bounded helper around exact live handler call after confirming call site"
