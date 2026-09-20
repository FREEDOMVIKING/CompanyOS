#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
TS="$(date +%Y%m%d_%H%M%S)"
BK="$HOME/companyos_runtime/backups/v27_5_$TS"
mkdir -p "$BK"
Q="companyos/runtime/autonomous_task_queue.py"
D="companyos/runtime/dependency_aware_dispatcher.py"
cp -p "$Q" "$BK/"
cp -p "$D" "$BK/"
echo "===== COMPANYOS V27.5 ====="

python - <<'PY'
from pathlib import Path
q=Path("companyos/runtime/autonomous_task_queue.py")
s=q.read_text()
a=s.index("    def bounded_candidates_window(")
b=s.index("    def bounded_candidates(", a)
replacement="""    def bounded_candidates_window(self, limit: int = 1000, offset: int = 0) -> list[TaskRecord]:
        # V27.5: operate on paths, never slice or len() a generator.
        limit = max(1, int(limit))
        offset = max(0, int(offset))
        files = sorted(self.root.glob("*.json"), key=lambda p: p.name)
        if not files:
            return []
        start = offset % len(files)
        tasks = []
        for i in range(min(limit, len(files))):
            path = files[(start + i) % len(files)]
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                tasks.append(TaskRecord(**data))
            except Exception:
                continue
        return tasks

    def task_file_count(self) -> int:
        return sum(1 for _ in self.root.glob("*.json"))

"""
q.write_text(s[:a]+replacement+s[b:])

d=Path("companyos/runtime/dependency_aware_dispatcher.py")
s=d.read_text()
a=s.index("    def dispatch_next(self) -> DispatchResult:")
replacement="""    def dispatch_next(self) -> DispatchResult:
        import os
        import time
        scan_limit = max(1, int(os.getenv("COMPANYOS_QUEUE_SCAN_LIMIT", "1000")))
        cursor_path = self.queue.root.parent / "dispatcher_scan_cursor.txt"
        try:
            cursor = int(cursor_path.read_text().strip()) if cursor_path.exists() else 0
        except Exception:
            cursor = 0

        if hasattr(self.queue, "bounded_candidates_window"):
            source = self.queue.bounded_candidates_window(scan_limit, cursor)
        elif hasattr(self.queue, "bounded_candidates"):
            source = self.queue.bounded_candidates(scan_limit)
        else:
            source = self.queue.all_tasks()[:scan_limit]

        try:
            total = self.queue.task_file_count() if hasattr(self.queue, "task_file_count") else len(self.queue.all_tasks())
            cursor_path.write_text(str((cursor + scan_limit) % max(1, total)))
        except Exception:
            pass

        now = time.time()
        candidates = [
            t for t in source
            if t.state == "QUEUED"
            and t.attempts < t.max_attempts
            and t.next_attempt_unix <= now
            and self._dependency_satisfied(t)
            and t.task_type in self.dispatcher.handlers
        ]
        if not candidates:
            return DispatchResult(False, None, None, None, "no_dependency_ready_task", None)

        candidates.sort(key=lambda t: (-int(t.priority), float(t.created_at_unix)))
        chosen = candidates[0]
        agent_name, handler = self.dispatcher.handlers[chosen.task_type]

        task = self.queue.load(chosen.task_id)
        if task.state != "QUEUED" or task.attempts >= task.max_attempts:
            return DispatchResult(False, task.task_id, None, task.state, "task_no_longer_eligible", None)
        if not self._dependency_satisfied(task):
            return DispatchResult(False, task.task_id, None, task.state, "dependency_no_longer_ready", None)

        task.state = "CLAIMED"
        task.assigned_agent = agent_name
        task.updated_at_unix = time.time()
        self.queue.save(task)
        self.queue.mark_running(task)
        try:
            result = handler(task)
            self.queue.complete(task, result)
            return DispatchResult(True, task.task_id, agent_name, task.state, "completed", result)
        except Exception as exc:
            self.queue.fail(task, f"{type(exc).__name__}:{str(exc)}", retry_delay_seconds=0)
            return DispatchResult(True, task.task_id, agent_name, task.state, "handler_failed", None)
"""
d.write_text(s[:a]+replacement)
PY

python -m py_compile "$Q" "$D"
echo "COMPILE=PASS"

python - <<'PY'
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue()
print("TASK_FILES=",q.task_file_count())
print("WINDOW_ROWS=",len(q.bounded_candidates_window(25,0)))
print("READ_ONLY_SMOKE=PASS")
PY

grep -q 'len(self.queue._iter_task_files())' "$D" && { echo "ABORT: old generator len remains"; exit 1; } || true
grep -q 'self.dispatcher.dispatch_next()' "$D" && { echo "ABORT: old full-rescan dispatch remains"; exit 1; } || true

echo "GENERATOR_LEN_BUG=REMOVED"
echo "EXACT_BOUNDED_DISPATCH=INSTALLED"
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_RESTARTED=NO"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "===== SUPERVISOR ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
echo "===== V27.5 PASS ====="
echo "Backup: $BK"
