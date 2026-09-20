#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"; export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
echo "===== COMPANYOS V62 QUEUE SPLIT-BRAIN GUARD ====="
F="companyos/runtime/autonomous_task_queue.py"
STAMP="$(date +%Y%m%d_%H%M%S)"
cp "$F" "$F.v62_backup_$STAMP"

python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/autonomous_task_queue.py")
s=p.read_text()
old="        indexed = self.kernel.idempotent_task(key)\n        if indexed:\n            try: return self.load(indexed)\n            except Exception: pass\n        for task in self.all_tasks():\n"
new="        indexed = self.kernel.idempotent_task(key)\n        if indexed:\n            try:\n                return self.load(indexed)\n            except FileNotFoundError:\n                raise RuntimeError(f\"durable_task_projection_missing:{indexed}:{key}\")\n            except Exception as exc:\n                raise RuntimeError(f\"durable_task_projection_unreadable:{indexed}:{key}:{type(exc).__name__}\") from exc\n        for task in self.all_tasks():\n"
if old not in s:
    raise SystemExit("V62_ABORT=target block not found; source changed")
p.write_text(s.replace(old,new,1))
print("PATCH_APPLIED=1")
PY

python -m py_compile "$F"

python - <<'PY'
import tempfile,time
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue,TaskRecord
root=Path(tempfile.mkdtemp())/"task_queue"; q=AutonomousTaskQueue(root); now=time.time()
t=TaskRecord("v62-test-id","v62:test:key","research",100,{"goal_id":"v62:goal:0","stage":"research"},"FAILED",None,3,3,now,now,now,None,"old")
q.save(t); q._path(t.task_id).unlink()
try:
    q.enqueue(task_type="research",payload={"goal_id":"v62:goal:0","stage":"research"},idempotency_key="v62:test:key")
except RuntimeError as e:
    ok=str(e).startswith("durable_task_projection_missing:")
    print("MISSING_PROJECTION_BLOCKED=",ok)
    if not ok: raise
else:
    raise SystemExit("V62_ABORT=duplicate enqueue was not blocked")
print("V62_SPLIT_BRAIN_GUARD=PASS")
PY

git diff -- "$F" | sed -n '1,160p'
