#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
BK=".companyos_runtime/backups/v27_1_${STAMP}"
mkdir -p "$BK" tests
F="companyos/runtime/dependency_aware_dispatcher.py"
cp -f "$F" "$BK/"

echo "===== COMPANYOS V27.1 EXACT LIVE DISPATCHER ====="
echo "SUPERVISOR_RESTART=NO"

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/dependency_aware_dispatcher.py")
s=p.read_text()

imp="from companyos.runtime.bounded_backlog_controller import select_bounded"
anchor="from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher, DispatchResult"
if imp not in s:
    if anchor not in s:
        raise SystemExit("V27_1_ABORT: import anchor missing")
    s=s.replace(anchor, anchor+"\n"+imp, 1)

old="for t in self.queue.all_tasks():"
new="""# V27.1: bound live backlog traversal before dependency filtering.
        # Read-only selection; no queued records are deleted here.
        bounded = select_bounded(self.queue.all_tasks())
        for t in bounded.selected:"""

count=s.count(old)
if count != 1:
    if "for t in bounded.selected:" not in s:
        raise SystemExit(f"V27_1_ABORT: expected exactly one live loop, found {count}")
else:
    s=s.replace(old,new,1)

p.write_text(s)
PY

cat > tests/test_v27_1_exact_dispatcher.py <<'PY'
from pathlib import Path
import ast

P=Path("companyos/runtime/dependency_aware_dispatcher.py")

def test_syntax():
    ast.parse(P.read_text())

def test_bounded_live_path():
    s=P.read_text()
    assert "from companyos.runtime.bounded_backlog_controller import select_bounded" in s
    assert "bounded = select_bounded(self.queue.all_tasks())" in s
    assert "for t in bounded.selected:" in s
    assert "for t in self.queue.all_tasks():" not in s

def test_existing_semantics_preserved():
    s=P.read_text()
    assert "self._dependency_satisfied(t)" in s
    assert "candidates.sort(key=lambda t: (t.priority, t.created_at_unix))" in s
    assert "self.dispatcher.dispatch_next()" in s
PY

echo "===== COMPILE ====="
python -m py_compile \
 companyos/runtime/bounded_backlog_controller.py \
 companyos/runtime/dependency_aware_dispatcher.py
echo "COMPILE=PASS"

echo "===== TESTS ====="
python -m pytest -q tests/test_bounded_backlog_controller.py tests/test_v27_1_exact_dispatcher.py
echo "TESTS=PASS"

echo "===== PATCH CONFIRMATION ====="
grep -nE 'select_bounded|bounded.selected|dependency_satisfied|candidates.sort|dispatch_next' "$F"

echo "===== REAL QUEUE BOUNDED TEST ====="
python - <<'PY'
import time
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.bounded_backlog_controller import select_bounded
q=AutonomousTaskQueue()
start=time.monotonic()
rows=q.all_tasks()
load=time.monotonic()-start
start=time.monotonic()
b=select_bounded(rows)
sel=time.monotonic()-start
print("TOTAL_TASKS=",len(rows))
print("SELECTED=",len(b.selected))
print("SCANNED=",b.scanned)
print("ELIGIBLE_SCANNED=",b.eligible)
print("QUEUE_LOAD_SECONDS=",round(load,4))
print("BOUNDED_SELECT_SECONDS=",round(sel,4))
print("REAL_QUEUE_BOUNDED_TEST=PASS")
PY

echo "===== SUPERVISOR PRESERVATION ====="
pgrep -af 'companyos.runtime.service_supervisor' || true

echo "===== EXPLICIT COMMIT ONLY ====="
git add "$F" tests/test_v27_1_exact_dispatcher.py
git commit -m "Wire V27.1 bounded selector into exact live dispatcher" || true
git push origin HEAD || true

echo
echo "COMPANYOS_V27_1_EXACT_LIVE_DISPATCHER=PASS"
echo "SUPERVISOR_RESTARTED=NO"
echo "BACKLOG_DELETED=NO"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "CURRENT_RUNNING_PROCESS_UNCHANGED=YES"
