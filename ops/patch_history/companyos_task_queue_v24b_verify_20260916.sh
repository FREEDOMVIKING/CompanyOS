#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/companyos"
PY="${PYTHON:-python}"

echo "===== COMPANYOS V24B QUEUE VERIFY ====="
echo "No supervisor restart. No finance/connector changes."

"$PY" -m py_compile \
  companyos/runtime/autonomous_task_queue.py \
  companyos/runtime/dependency_aware_dispatcher.py
echo "COMPILE=PASS"

echo "===== ISOLATED CONTRACT TEST ====="
"$PY" - <<'PY'
import tempfile
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

with tempfile.TemporaryDirectory() as d:
    q = AutonomousTaskQueue(root=Path(d))

    t = q.enqueue(
        task_type="research",
        payload={"goal_id": "g1", "stage": "research"},
        priority=1,
    )
    t.state = "COMPLETED"
    q.save(t)

    q.enqueue(
        task_type="planning",
        payload={"goal_id": "g1", "stage": "planning"},
        priority=1,
    )

    (Path(d) / "malformed.json").write_text(
        '{"task_id":"broken"} trailing',
        encoding="utf-8",
    )

    assert q.has_completed_goal_stage("g1", "research") is True
    assert q.has_completed_goal_stage("g1", "planning") is False

    readable = q.all_tasks()
    assert len(readable) == 2, len(readable)

print("QUEUE_CONTRACT_TEST=PASS")
PY

echo "===== REAL QUEUE STREAM TEST ====="
"$PY" - <<'PY'
import time
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

q = AutonomousTaskQueue()
start = time.monotonic()
count = sum(1 for _ in q._iter_task_files())
elapsed = time.monotonic() - start

print("READABLE_TASKS=", count)
print("STREAM_SCAN_SECONDS=", round(elapsed, 3))
print("REAL_QUEUE_STREAM=PASS")
PY

echo "===== REAL DEPENDENCY LOOKUP SMOKE TEST ====="
"$PY" - <<'PY'
import time
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

q = AutonomousTaskQueue()
start = time.monotonic()
result = q.has_completed_goal_stage(
    "__companyos_v24b_nonexistent_goal__",
    "__nonexistent_stage__",
)
elapsed = time.monotonic() - start

assert result is False
print("DEPENDENCY_LOOKUP_RESULT=", result)
print("DEPENDENCY_LOOKUP_SECONDS=", round(elapsed, 3))
print("DEPENDENCY_LOOKUP_SMOKE=PASS")
PY

echo "===== MALFORMED RECORD RECHECK ====="
"$PY" - <<'PY'
from pathlib import Path
import json

root = Path.home() / ".companyos_runtime" / "task_queue"
bad = []
for p in root.glob("*.json"):
    try:
        json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        bad.append((p.name, type(e).__name__))

print("MALFORMED_REMAINING=", len(bad))
for name, kind in bad[:20]:
    print("BAD_RECORD=", name, kind)

if bad:
    raise SystemExit("MALFORMED_RECORDS_STILL_PRESENT")
print("MALFORMED_RECHECK=PASS")
PY

echo "===== SUPERVISOR PRESERVATION ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
echo "HEALTHY_SUPERVISOR_RESTARTED=NO"

echo "===== PATCH STATE ====="
git diff -- companyos/runtime/autonomous_task_queue.py \
  companyos/runtime/dependency_aware_dispatcher.py || true

echo "COMPANYOS_TASK_QUEUE_V24B=PASS"
echo "NEXT=controlled durable execution cycle"
