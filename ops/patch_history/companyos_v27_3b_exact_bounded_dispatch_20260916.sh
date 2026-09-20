#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V27.3B EXACT BOUNDED DISPATCH ====="
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".companyos_runtime/backups/v27_3b_$STAMP"
mkdir -p "$BACKUP"
cp companyos/runtime/autonomous_task_queue.py "$BACKUP/"
cp companyos/runtime/dependency_aware_dispatcher.py "$BACKUP/"
echo "BACKUP=$BACKUP"

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/dependency_aware_dispatcher.py")
s=p.read_text()
start=s.find("    def dispatch_next(self) -> DispatchResult:")
if start < 0: raise SystemExit("PATCH_ABORT: dispatch_next not found")
end=s.find("\n    def ", start+5)
if end < 0: end=len(s)
patch='    def dispatch_next(self) -> DispatchResult:\n        import os\n        scan_limit = max(1, int(os.getenv("COMPANYOS_QUEUE_SCAN_LIMIT", "1000")))\n        source = self.queue.bounded_candidates(scan_limit) if hasattr(self.queue, "bounded_candidates") else self.queue.all_tasks()[:scan_limit]\n        candidates = [t for t in source if t.state == "QUEUED" and t.attempts < t.max_attempts and self._dependency_satisfied(t) and t.task_type in self.dispatcher.handlers]\n        if not candidates:\n            return DispatchResult(False, None, None, None, "no_dependency_ready_task", None)\n        candidates.sort(key=lambda t: (-t.priority, t.created_at_unix))\n        chosen = candidates[0]\n        original_priority = chosen.priority\n        chosen.priority = 10**9\n        self.queue.save(chosen)\n        try:\n            result = self.dispatcher.dispatch_next()\n        finally:\n            try:\n                saved = self.queue.load(chosen.task_id)\n                if saved.state == "QUEUED":\n                    saved.priority = original_priority\n                    self.queue.save(saved)\n            except Exception:\n                pass\n        return result\n'
p.write_text(s[:start]+patch+s[end:])
print("DISPATCH_PATCH=PASS")
PY

python -m py_compile companyos/runtime/autonomous_task_queue.py companyos/runtime/dependency_aware_dispatcher.py
echo "COMPILE=PASS"

python - <<'PY'
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.dependency_aware_dispatcher import DependencyAwareDispatcher
assert hasattr(AutonomousTaskQueue,"bounded_candidates")
assert hasattr(DependencyAwareDispatcher,"dispatch_next")
q=AutonomousTaskQueue()
rows=q.bounded_candidates(1000)
assert len(rows)<=1000
print("API_CONTRACT=PASS")
print("BOUNDED_ROWS:",len(rows))
PY

SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
OLD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | head -1 || true)"
echo "SUPERVISOR_BEFORE=${SUP:-NONE}"
echo "CONTINUOUS_BEFORE=${OLD:-NONE}"
[ -n "$SUP" ] || { echo "ABORT=SUPERVISOR_NOT_RUNNING"; exit 1; }
if [ -n "$OLD" ]; then kill -TERM "$OLD" || true; fi
sleep 8
SUP2="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
NEW="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | head -1 || true)"
echo "SUPERVISOR_AFTER=${SUP2:-NONE}"
echo "CONTINUOUS_AFTER=${NEW:-NONE}"
[ -n "$SUP2" ] || { echo "FAIL=SUPERVISOR_STOPPED"; exit 1; }
[ -n "$NEW" ] || { echo "FAIL=CONTINUOUS_NOT_RESTARTED"; exit 1; }
echo "===== V27.3B PASS ====="
echo "No queue records deleted; dependency gates retained."
