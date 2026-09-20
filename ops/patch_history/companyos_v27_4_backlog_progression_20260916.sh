#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V27.4 BACKLOG PROGRESSION ====="
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".companyos_runtime/backups/v27_4_$STAMP"
mkdir -p "$BACKUP"
cp companyos/runtime/dependency_aware_dispatcher.py "$BACKUP/"
cp companyos/runtime/autonomous_task_queue.py "$BACKUP/"
echo "BACKUP=$BACKUP"
SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
[ -n "$SUP" ] || { echo "ABORT=SUPERVISOR_NOT_RUNNING"; exit 1; }
echo "SUPERVISOR=$SUP"

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/autonomous_task_queue.py")
s=p.read_text()
if "def bounded_candidates_window(" not in s:
    anchor="    def bounded_candidates("
    pos=s.find(anchor)
    if pos < 0: raise SystemExit("PATCH_ABORT: bounded_candidates not found")
    method = '    def bounded_candidates_window(self, limit: int = 1000, offset: int = 0) -> list[TaskRecord]:\n        limit=max(1,int(limit)); offset=max(0,int(offset))\n        files=self._iter_task_files() if hasattr(self,"_iter_task_files") else list(self.root.glob("*.json"))\n        if not files: return []\n        start=offset % len(files); ordered=files[start:]+files[:start]; tasks=[]\n        for path in ordered[:limit]:\n            try:\n                data=json.loads(path.read_text(encoding="utf-8")); tasks.append(TaskRecord(**data))\n            except Exception: continue\n        return tasks\n\n'
    p.write_text(s[:pos]+method+s[pos:])
    print("QUEUE_WINDOW_PATCH=PASS")
else: print("QUEUE_WINDOW_PATCH=ALREADY_PRESENT")

p=Path("companyos/runtime/dependency_aware_dispatcher.py"); s=p.read_text()
old='        source = self.queue.bounded_candidates(scan_limit) if hasattr(self.queue, "bounded_candidates") else self.queue.all_tasks()[:scan_limit]\n        candidates = [t for t in source if t.state == "QUEUED" and t.attempts < t.max_attempts and self._dependency_satisfied(t) and t.task_type in self.dispatcher.handlers]\n'
new='        cursor_path = self.queue.root.parent / "dispatcher_scan_cursor.txt"\n        try:\n            cursor = int(cursor_path.read_text().strip()) if cursor_path.exists() else 0\n        except Exception:\n            cursor = 0\n        if hasattr(self.queue, "bounded_candidates_window"):\n            source = self.queue.bounded_candidates_window(scan_limit, cursor)\n        elif hasattr(self.queue, "bounded_candidates"):\n            source = self.queue.bounded_candidates(scan_limit)\n        else:\n            source = self.queue.all_tasks()[:scan_limit]\n        try:\n            total = len(self.queue._iter_task_files()) if hasattr(self.queue, "_iter_task_files") else len(self.queue.all_tasks())\n            cursor_path.write_text(str((cursor + scan_limit) % max(1,total)))\n        except Exception:\n            pass\n        candidates = [t for t in source if t.state == "QUEUED" and t.attempts < t.max_attempts and self._dependency_satisfied(t) and t.task_type in self.dispatcher.handlers]\n'
if old in s:
    p.write_text(s.replace(old,new,1)); print("ROTATING_DISPATCH_PATCH=PASS")
elif "dispatcher_scan_cursor.txt" in s: print("ROTATING_DISPATCH_PATCH=ALREADY_PRESENT")
else: raise SystemExit("PATCH_ABORT: V27.3B source not found")
PY

python -m py_compile companyos/runtime/autonomous_task_queue.py companyos/runtime/dependency_aware_dispatcher.py
echo "COMPILE=PASS"
python - <<'PY'
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue(); a=q.bounded_candidates_window(1000,0); b=q.bounded_candidates_window(1000,1000)
assert len(a)<=1000 and len(b)<=1000
print("WINDOW_CONTRACT=PASS"); print("WINDOW0:",len(a)); print("WINDOW1000:",len(b))
PY

OLD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | head -1 || true)"
echo "CONTINUOUS_BEFORE=${OLD:-NONE}"
[ -z "$OLD" ] || kill -TERM "$OLD" || true
sleep 8
SUP2="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
NEW="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | head -1 || true)"
echo "SUPERVISOR_AFTER=${SUP2:-NONE}"
echo "CONTINUOUS_AFTER=${NEW:-NONE}"
[ -n "$SUP2" ] || { echo "FAIL=SUPERVISOR_STOPPED"; exit 1; }
[ -n "$NEW" ] || { echo "FAIL=CONTINUOUS_NOT_RESTARTED"; exit 1; }
echo "===== V27.4 PASS ====="
echo "Rotating bounded backlog scan active; no queue records deleted."
