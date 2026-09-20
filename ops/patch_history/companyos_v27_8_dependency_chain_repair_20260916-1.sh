#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$HOME/companyos"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$HOME/.companyos_runtime/backups/v27_8_$STAMP"
mkdir -p "$BACKUP"
echo "===== COMPANYOS V27.8 DEPENDENCY CHAIN REPAIR ====="
cp companyos/runtime/dependency_aware_dispatcher.py "$BACKUP/"
python - <<'PY'
from pathlib import Path
p=Path("companyos/runtime/dependency_aware_dispatcher.py")
s=p.read_text()
needle='        return self.queue.has_completed_goal_stage(goal_id, dep)'
repl='        if not goal_id:\n            return True\n\n        return self.queue.has_completed_goal_stage(goal_id, dep)'
if needle in s and "if not goal_id:" not in s: s=s.replace(needle,repl,1)
elif "if not goal_id:" not in s: raise SystemExit("V27_8_ABORT: dependency source changed")
p.write_text(s)
PY
python -m py_compile companyos/runtime/dependency_aware_dispatcher.py
echo "COMPILE=PASS"
echo "===== DEPENDENCY AUDIT ====="
python - <<'PY'
from collections import Counter
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.default_specialist_registry import register_default_specialists
from companyos.runtime.dependency_aware_dispatcher import DependencyAwareDispatcher
q=AutonomousTaskQueue(); b=AutonomousTaskDispatcher(q); register_default_specialists(b); d=DependencyAwareDispatcher(b)
c=Counter()
for t in q.all_tasks():
    if str(t.state).upper()!="QUEUED": continue
    if t.attempts>=t.max_attempts: r="max_attempts"
    elif t.task_type not in b.handlers: r="missing_handler"
    else:
        try: r="execution_ready" if d._dependency_satisfied(t) else "dependency_blocked"
        except Exception as e: r="dependency_error:"+type(e).__name__
    c[r]+=1
print("BLOCKERS=",dict(c)); print("REGISTERED_HANDLERS=",sorted(b.handlers))
PY
OLDPID="$(pgrep -f 'companyos.runtime.continuous_goal_runtime' | tail -1 || true)"
echo "CONTINUOUS_OLD_PID=${OLDPID:-none}"
if [ -n "${OLDPID:-}" ]; then kill "$OLDPID" 2>/dev/null || true; sleep 8; fi
echo "===== SUPERVISOR PRESERVED ====="
pgrep -af "companyos.runtime.service_supervisor" || true
echo "===== 45 SECOND LIVE TEST ====="
python - <<'PY'
import time
from collections import Counter
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
def snap(): return Counter(str(t.state).upper() for t in AutonomousTaskQueue().all_tasks())
a=snap(); print("BEFORE=",dict(a)); time.sleep(45); b=snap(); print("AFTER=",dict(b))
cd=b.get("COMPLETED",0)-a.get("COMPLETED",0); qd=b.get("QUEUED",0)-a.get("QUEUED",0)
print("COMPLETED_DELTA=",cd); print("QUEUED_DELTA=",qd); print("LIVE_PROGRESSION=" + ("PASS" if cd>0 else "STILL_BLOCKED"))
PY
git add companyos/runtime/dependency_aware_dispatcher.py
if ! git diff --cached --quiet; then git commit -m "V27.8 repair legacy dependency deadlocks"; git push origin "$(git branch --show-current)"; fi
echo "===== V27.8 COMPLETE ====="
echo "QUEUE_RECORDS_DELETED=0"
echo "SUPERVISOR_INTENTIONAL_RESTART=NO"
