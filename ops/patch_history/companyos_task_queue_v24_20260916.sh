#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
PY="${PYTHON:-python}"
echo "===== COMPANYOS V24 QUEUE RECOVERY ====="
STAMP="$(date +%Y%m%d_%H%M%S)"
B="$HOME/.companyos_runtime/v24_backup_$STAMP"
mkdir -p "$B"
cp companyos/runtime/autonomous_task_queue.py companyos/runtime/dependency_aware_dispatcher.py "$B/"
python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/autonomous_task_queue.py")
s=p.read_text()
needle="    def all_tasks(self) -> list[TaskRecord]:\n"
a=s.index(needle); b=s.index("    def find_by_idempotency_key",a)
replacement='''    def _iter_task_files(self):
        for path in self.root.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                yield TaskRecord(**data)
            except Exception:
                continue

    def all_tasks(self) -> list[TaskRecord]:
        return list(self._iter_task_files())

    def has_completed_goal_stage(self, goal_id: str, stage: str) -> bool:
        for task in self._iter_task_files():
            payload = task.payload if isinstance(task.payload, dict) else {}
            if payload.get("goal_id") == goal_id and payload.get("stage") == stage and task.state == "COMPLETED":
                return True
        return False

'''
p.write_text(s[:a]+replacement+s[b:])

p=Path("companyos/runtime/dependency_aware_dispatcher.py")
s=p.read_text()
a=s.index("        for candidate in self.queue.all_tasks():")
b=s.index("\n        return False",a)+len("\n        return False")
p.write_text(s[:a]+"        return self.queue.has_completed_goal_stage(goal_id, dep)"+s[b:])
print("SOURCE_PATCH=PASS")
PY
"$PY" -m py_compile companyos/runtime/autonomous_task_queue.py companyos/runtime/dependency_aware_dispatcher.py
echo "COMPILE=PASS"
python - <<'PY'
from pathlib import Path
import json,shutil,time
r=Path.home()/".companyos_runtime"/"task_queue"
q=Path.home()/".companyos_runtime"/"task_queue_quarantine"/time.strftime("%Y%m%d_%H%M%S")
bad=[]
for p in r.glob("*.json"):
    try: json.loads(p.read_text(encoding="utf-8"))
    except Exception as e: bad.append((p,type(e).__name__))
if bad:q.mkdir(parents=True,exist_ok=True)
for p,e in bad:
    shutil.move(str(p),str(q/p.name)); print("QUARANTINED",p.name,e)
print("QUARANTINED_COUNT=",len(bad))
PY
python - <<'PY'
import tempfile
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
with tempfile.TemporaryDirectory() as d:
 q=AutonomousTaskQueue(root=Path(d))
 t=q.enqueue("research",{"goal_id":"g1","stage":"research"},priority=1);t.state="COMPLETED";q.save(t)
 q.enqueue("planning",{"goal_id":"g1","stage":"planning"},priority=1)
 (Path(d)/"bad.json").write_text('{"x":1} trailing')
 assert q.has_completed_goal_stage("g1","research")
 assert not q.has_completed_goal_stage("g1","planning")
 assert len(q.all_tasks())==2
print("QUEUE_TEST=PASS")
PY
python - <<'PY'
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
q=AutonomousTaskQueue()
print("READABLE_TASKS=",sum(1 for _ in q._iter_task_files()))
print("REAL_QUEUE_SCAN=PASS")
PY
pgrep -af "companyos.runtime.service_supervisor" || true
echo "HEALTHY_SUPERVISOR_RESTARTED=NO"
git add companyos/runtime/autonomous_task_queue.py companyos/runtime/dependency_aware_dispatcher.py
git diff --cached --quiet || git commit -m "Harden persistent task queue lookup V24"
git push origin "$(git branch --show-current)" || echo "GIT_PUSH_WARNING"
echo "COMPANYOS_TASK_QUEUE_V24=PASS"
echo "V24 intentionally does not run durable recovery yet."
