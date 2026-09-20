#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
BK=".companyos_runtime/backups/v27_${STAMP}"
mkdir -p "$BK" tests
echo "===== COMPANYOS V27 — LIVE BOUNDED DISPATCHER ====="
echo "Supervisor restart: NO"

for f in companyos/runtime/dependency_aware_dispatcher.py companyos/runtime/bounded_backlog_controller.py; do
  [ -f "$f" ] && cp -f "$f" "$BK/"
done

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/dependency_aware_dispatcher.py")
s=p.read_text()
if "from companyos.runtime.bounded_backlog_controller import select_bounded" not in s:
    marker="from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher, DispatchResult"
    if marker not in s: raise SystemExit("V27_ABORT: dispatcher import marker not found")
    s=s.replace(marker, marker+"\nfrom companyos.runtime.bounded_backlog_controller import select_bounded",1)

old="candidates = []\n        for candidate in self.queue.all_tasks():"
new="""candidates = []
        # V27: never walk the entire persistent backlog in a live dispatch cycle.
        # The selector is read-only: no tasks are deleted or mutated here.
        _bounded = select_bounded(self.queue.all_tasks())
        for candidate in _bounded.selected:"""
if old not in s:
    if "_bounded = select_bounded(" not in s:
        raise SystemExit("V27_ABORT: exact dispatcher loop marker not found; source left unchanged")
else:
    s=s.replace(old,new,1)
p.write_text(s)
PY

cat > tests/test_v27_live_bounded_dispatcher.py <<'PY'
from pathlib import Path
def test_live_dispatcher_uses_bounded_selector():
    s=Path("companyos/runtime/dependency_aware_dispatcher.py").read_text()
    assert "from companyos.runtime.bounded_backlog_controller import select_bounded" in s
    assert "_bounded = select_bounded(self.queue.all_tasks())" in s
    assert "for candidate in _bounded.selected:" in s
def test_unbounded_loop_removed():
    s=Path("companyos/runtime/dependency_aware_dispatcher.py").read_text()
    assert "for candidate in self.queue.all_tasks():" not in s
PY

echo "===== COMPILE ====="
python -m py_compile companyos/runtime/bounded_backlog_controller.py \
 companyos/runtime/dependency_aware_dispatcher.py
echo "COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_bounded_backlog_controller.py tests/test_v27_live_bounded_dispatcher.py
echo "TESTS=PASS"

echo "===== ISOLATED DISPATCH SMOKE TEST ====="
python - <<'PY'
import time
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.bounded_backlog_controller import select_bounded
q=AutonomousTaskQueue()
t=time.monotonic(); rows=q.all_tasks(); load=time.monotonic()-t
t=time.monotonic(); x=select_bounded(rows); choose=time.monotonic()-t
print("TOTAL_TASKS=",len(rows))
print("BOUNDED_SELECTED=",len(x.selected))
print("BOUNDED_SCANNED=",x.scanned)
print("QUEUE_LOAD_SECONDS=",round(load,4))
print("SELECTION_SECONDS=",round(choose,4))
assert len(x.selected) <= int(__import__("os").getenv("COMPANYOS_BACKLOG_BATCH_SIZE","32"))
print("BOUNDED_SMOKE=PASS")
PY

echo "===== SUPERVISOR PRESERVATION ====="
pgrep -af 'companyos.runtime.service_supervisor' || true

echo "===== EXPLICIT GIT FILES ONLY ====="
git add companyos/runtime/dependency_aware_dispatcher.py \
 tests/test_v27_live_bounded_dispatcher.py
git commit -m "Wire V27 bounded selection into live dispatcher" || true
git push origin HEAD || true

echo
echo "COMPANYOS_V27_LIVE_BOUNDED_DISPATCHER=PASS"
echo "SUPERVISOR_RESTARTED=NO"
echo "BACKLOG_DELETED=NO"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "NOTE=Existing Python services keep their loaded module until their normal restart; source is now ready for the next safe service recycle."
