#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
TARGET="companyos/runtime/dependency_aware_dispatcher.py"
QUEUE="companyos/runtime/autonomous_task_queue.py"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="${TARGET}.v27_2_backup_${STAMP}"
LIMIT="${COMPANYOS_DISPATCH_SCAN_LIMIT:-1000}"
echo "===== COMPANYOS V27.2 BOUNDED QUEUE DISPATCHER ====="
echo "Supervisor will NOT be restarted."
cp -p "$TARGET" "$BACKUP"
python - "$TARGET" "$LIMIT" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); limit=int(sys.argv[2]); src=p.read_text()
start=src.find("        candidates = [")
if start < 0:
    print("V27_2_ABORT: candidates block not found"); raise SystemExit(20)
end=src.find("\n        ]", start)
if end < 0:
    print("V27_2_ABORT: candidates block end not found"); raise SystemExit(21)
end += len("\n        ]")
block=src[start:end]
required=["self.queue.all_tasks()", 't.state == "QUEUED"', "self._dependency_satisfied(t)", "self.dispatcher.handlers"]
if not all(x in block for x in required):
    print("V27_2_ABORT: located block does not match live dispatcher contract"); raise SystemExit(22)
new = """        # V27.2 bounded filesystem scan; no task records are deleted.
        candidates = []
        scanned = 0
        task_root = getattr(self.queue, "root", None)
        if task_root is not None:
            try:
                task_files = sorted(task_root.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
            except OSError:
                task_files = list(task_root.glob("*.json"))
            for task_path in task_files:
                if scanned >= LIMIT_PLACEHOLDER:
                    break
                scanned += 1
                try:
                    t = self.queue.load(task_path.stem)
                except Exception:
                    continue
                if (t.state == "QUEUED"
                    and t.attempts < t.max_attempts
                    and self._dependency_satisfied(t)
                    and t.task_type in self.dispatcher.handlers):
                    candidates.append(t)
        else:
            for t in self.queue.all_tasks():
                if scanned >= LIMIT_PLACEHOLDER:
                    break
                scanned += 1
                if (t.state == "QUEUED"
                    and t.attempts < t.max_attempts
                    and self._dependency_satisfied(t)
                    and t.task_type in self.dispatcher.handlers):
                    candidates.append(t)""".replace("LIMIT_PLACEHOLDER", str(limit))
p.write_text(src[:start]+new+src[end:])
print("PATCH=PASS"); print("SCAN_LIMIT="+str(limit))
PY
rollback(){ echo "V27_2_ROLLBACK=YES"; cp -p "$BACKUP" "$TARGET"; }
trap 'rc=$?; if [ $rc -ne 0 ]; then rollback; fi; exit $rc' EXIT
echo "===== COMPILE ====="
python -m py_compile "$TARGET" "$QUEUE"
echo "COMPILE=PASS"
echo "===== STATIC CONTRACT ====="
python - <<'PY'
from pathlib import Path
s=Path("companyos/runtime/dependency_aware_dispatcher.py").read_text()
for x in ["scanned >= 1000",'glob("*.json")',"self.queue.load(task_path.stem)","self._dependency_satisfied(t)","self.dispatcher.dispatch_next()"]:
    assert x in s, x
print("STATIC_CONTRACT=PASS")
PY
echo "===== REAL QUEUE READ-ONLY TIMING ====="
python - <<'PY'
import time
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue(); root=Path(q.root)
files=sorted(root.glob("*.json"),key=lambda p:p.stat().st_mtime,reverse=True)[:1000]
t0=time.monotonic(); good=bad=0
for p in files:
    try: q.load(p.stem); good+=1
    except Exception: bad+=1
dt=time.monotonic()-t0
print("SCANNED=",len(files)); print("READABLE=",good); print("MALFORMED_SKIPPED=",bad); print("SECONDS=",round(dt,3))
assert dt < 30
print("REAL_QUEUE_BOUNDED_TEST=PASS")
PY
echo "===== SUPERVISOR PRESERVATION ====="
pgrep -af 'companyos.runtime.service_supervisor' || true
echo "SUPERVISOR_RESTARTED=NO"
trap - EXIT
echo "COMPANYOS_V27_2_BOUNDED_QUEUE_DISPATCHER=PASS"
echo "BACKUP=$BACKUP"
echo "NOTE=Existing Python processes retain loaded code until their normal restart/reload."
