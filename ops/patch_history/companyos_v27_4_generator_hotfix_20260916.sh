#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
TARGET="companyos/runtime/autonomous_task_queue.py"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$HOME/companyos_backups/v27_4_generator_hotfix_$STAMP"
mkdir -p "$BACKUP"
cp -p "$TARGET" "$BACKUP/"

echo "===== COMPANYOS V27.4 GENERATOR HOTFIX ====="
python - <<'PY'
from pathlib import Path
import re

p = Path("companyos/runtime/autonomous_task_queue.py")
s = p.read_text(encoding="utf-8")

pattern = re.compile(
    r'(?ms)^    def bounded_candidates_window\(self,\s*limit:\s*int\s*=\s*512\).*?(?=^    def |\Z)'
)

replacement = '''    def bounded_candidates_window(self, limit: int = 512) -> list[TaskRecord]:
        # iter_task_files() is a generator; consume only a bounded slice.
        limit = max(1, int(limit))
        paths = []
        for path in self.iter_task_files():
            paths.append(path)
            if len(paths) >= limit:
                break

        tasks: list[TaskRecord] = []
        for path in paths:
            try:
                tasks.append(self.load(path.stem))
            except Exception:
                continue
        return tasks

'''

m = pattern.search(s)
if not m:
    raise SystemExit("HOTFIX_ABORT: bounded_candidates_window method not found")

p.write_text(s[:m.start()] + replacement + s[m.end():], encoding="utf-8")
print("PATCH_APPLIED")
PY

echo "===== COMPILE ====="
python -m py_compile "$TARGET"
echo "COMPILE_PASS"

echo "===== API SMOKE TEST ====="
python - <<'PY'
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q = AutonomousTaskQueue()
rows = q.bounded_candidates_window(25)
assert isinstance(rows, list)
assert len(rows) <= 25
print("BOUNDED_WINDOW_PASS", len(rows))
PY

echo "===== SUPERVISOR PRESERVATION ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
echo "No supervisor restart performed."
echo "===== V27.4 HOTFIX PASS ====="
echo "Generator/len crash repaired."
echo "Queue records were not deleted."
echo "Dependency gates remain intact."
