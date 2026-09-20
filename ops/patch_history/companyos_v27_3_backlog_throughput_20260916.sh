#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
echo "===== COMPANYOS V27.3 BACKLOG THROUGHPUT ====="
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".companyos_runtime/backups/v27_3_$STAMP"
mkdir -p "$BACKUP"
cp companyos/runtime/autonomous_task_queue.py "$BACKUP/"
cp companyos/runtime/dependency_aware_dispatcher.py "$BACKUP/"
echo "BACKUP=$BACKUP"
python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/autonomous_task_queue.py")
s=p.read_text()
marker="    def has_completed_goal_stage("
if "def bounded_candidates(" not in s:
    pos=s.find(marker)
    if pos < 0: raise SystemExit("QUEUE_PATCH_ABORT: marker not found")
    m="    def bounded_candidates(self, limit: int = 512) -> list[TaskRecord]:\n"
    m+="        limit = max(1, int(limit))\n"
    m+="        candidates = []\n"
    m+="        for task in self._iter_task_files():\n"
    m+="            if task.state != \"QUEUED\":\n                continue\n"
    m+="            if task.attempts >= task.max_attempts:\n                continue\n"
    m+="            candidates.append(task)\n"
    m+="        candidates.sort(key=lambda t: (-int(t.priority), float(t.created_at_unix)))\n"
    m+="        return candidates[:limit]\n\n"
    p.write_text(s[:pos]+m+s[pos:])
    print("QUEUE_PATCH=APPLIED")
else: print("QUEUE_PATCH=ALREADY_PRESENT")
PY
python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/dependency_aware_dispatcher.py")
s=p.read_text()
needle="        candidates = [\n            t for t in self.queue.all_tasks()"
if "self.queue.bounded_candidates(scan_limit)" not in s:
    if needle not in s: raise SystemExit("DISPATCH_PATCH_ABORT: V27.2 block not found")
    replacement="        scan_limit = int(__import__(\"os\").getenv(\"COMPANYOS_QUEUE_SCAN_LIMIT\", \"512\"))\n        source = self.queue.bounded_candidates(scan_limit) if hasattr(self.queue, \"bounded_candidates\") else self.queue.all_tasks()\n        candidates = [\n            t for t in source"
    s=s.replace(needle,replacement,1)
    p.write_text(s)
    print("DISPATCH_PATCH=APPLIED")
else: print("DISPATCH_PATCH=ALREADY_PRESENT")
PY
echo "===== COMPILE ====="
python -m py_compile companyos/runtime/autonomous_task_queue.py companyos/runtime/dependency_aware_dispatcher.py
echo "COMPILE=PASS"
echo "===== LIVE BOUNDED READ ====="
python - <<'PY'
import time
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue()
t=time.time(); rows=q.bounded_candidates(512)
print("BOUNDED_ROWS:",len(rows)); print("SECONDS:",round(time.time()-t,3))
PY
echo "===== TARGETED CHILD RELOAD ====="
SUP="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
OLD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | head -1 || true)"
echo "SUPERVISOR_BEFORE=${SUP:-NONE}"
echo "CONTINUOUS_BEFORE=${OLD:-NONE}"
if [ -n "${OLD:-}" ]; then kill -TERM "$OLD" || true; sleep 8; fi
SUP2="$(pgrep -f 'companyos.runtime.service_supervisor' | head -1 || true)"
NEW="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | head -1 || true)"
echo "SUPERVISOR_AFTER=${SUP2:-NONE}"
echo "CONTINUOUS_AFTER=${NEW:-NONE}"
[ -n "$SUP2" ] || { echo "FAIL=SUPERVISOR_NOT_RUNNING"; exit 1; }
[ -n "$NEW" ] || { echo "FAIL=CONTINUOUS_NOT_RESTARTED"; exit 1; }
echo "===== V27.3 COMPLETE ====="
echo "No queue records deleted; dependency checks remain active."
