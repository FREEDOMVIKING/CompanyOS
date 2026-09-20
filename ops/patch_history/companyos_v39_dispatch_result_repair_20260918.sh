#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
cd "$HOME/companyos"
RT="$HOME/.companyos_runtime"
B="$RT/backups/v39_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$B"
D="companyos/runtime/autonomous_task_dispatcher.py"
cp -a "$D" "$B/"
echo "===== COMPANYOS V39 DISPATCH RESULT REPAIR ====="

echo "===== PREFLIGHT ====="
python -m py_compile "$D" companyos/runtime/lease_execution_guard.py companyos/runtime/worker_lease_store.py
grep -q 'V35_1_FENCED_HANDLER_CALL' "$D" || { echo "ABORT=V35.1_contract_missing"; exit 20; }
echo "PREFLIGHT=PASS"

echo "===== REBUILD dispatch_task CLEANLY ====="
python - <<'PY'
from pathlib import Path
import ast

p=Path("companyos/runtime/autonomous_task_dispatcher.py")
src=p.read_text()
tree=ast.parse(src)

klass=None
method=None
for node in tree.body:
    if isinstance(node, ast.ClassDef) and node.name=="AutonomousTaskDispatcher":
        klass=node
        for child in node.body:
            if isinstance(child, ast.FunctionDef) and child.name=="dispatch_task":
                method=child
                break
        break
if method is None:
    raise SystemExit("ABORT=dispatch_task_not_found")

lines=src.splitlines()
start=method.lineno-1
end=method.end_lineno

replacement = [
'    def dispatch_task(self, task: TaskRecord) -> DispatchResult:',
'        # V39_CLEAN_FENCED_DISPATCH',
'        now = time.time()',
'        task = self.queue.load(task.task_id)',
'',
'        if task.state != "QUEUED":',
'            return DispatchResult(False, task.task_id, None, task.state, "task_not_queued", None)',
'        if task.attempts >= task.max_attempts:',
'            return DispatchResult(False, task.task_id, None, task.state, "attempts_exhausted", None)',
'        if task.next_attempt_unix > now:',
'            return DispatchResult(False, task.task_id, None, task.state, "retry_not_due", None)',
'        if task.task_type not in self.handlers:',
'            return DispatchResult(False, task.task_id, None, task.state, "unsupported_task_type", None)',
'',
'        agent, handler = self.handlers[task.task_type]',
'        task.state = "CLAIMED"',
'        task.assigned_agent = agent',
'        task.updated_at_unix = now',
'        self.queue.save(task)',
'        task = self.queue.mark_running(task)',
'',
'        try:',
'            guard = LeaseExecutionGuard(self.queue.kernel.db_path)',
'            task_id = str(task.task_id)',
'            owner = "dispatcher-" + str(id(self))',
'            ok, result, error = guard.execute(',
'                task_id,',
'                owner,',
'                lambda: handler(task),',
'            )',
'            if not ok:',
'                raise RuntimeError(error or "leased_execution_failed")',
'',
'            task = self.queue.complete(task, result)',
'            return DispatchResult(True, task.task_id, agent, task.state, "completed", result)',
'        except Exception as exc:',
'            task = self.queue.fail(',
'                task,',
'                f"{type(exc).__name__}:{exc}",',
'                retry_delay_seconds=30,',
'            )',
'            return DispatchResult(True, task.task_id, agent, task.state, "handler_failed", None)',
]

newlines = lines[:start] + replacement + lines[end:]
new = "\n".join(newlines) + "\n"

imp="from companyos.runtime.lease_execution_guard import LeaseExecutionGuard"
if imp not in new:
    nl=new.splitlines()
    insert=0
    while insert < len(nl) and (not nl[insert].strip() or nl[insert].startswith("from __future__")):
        insert += 1
    nl.insert(insert, imp)
    new="\n".join(nl)+"\n"

ast.parse(new)
p.write_text(new)
print("DISPATCH_METHOD_REBUILT=PASS")
PY

python -m py_compile "$D"
echo "COMPILE=PASS"

cat > tests/test_v39_dispatch_result_repair.py <<'PY'
import tempfile
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher

def test_success_result_is_defined_and_persisted():
    with tempfile.TemporaryDirectory() as td:
        q=AutonomousTaskQueue(Path(td)/"task_queue")
        d=AutonomousTaskDispatcher(q)
        d.register(task_type="research",agent_name="r",handler=lambda task: {"answer":42})
        t=q.enqueue(task_type="research",payload={"goal_id":"g","stage":"research"},idempotency_key="v39-ok")
        r=d.dispatch_task(t)
        assert r.dispatched is True
        assert r.reason=="completed"
        assert r.result=={"answer":42}
        loaded=q.load(t.task_id)
        assert loaded.state=="COMPLETED"
        assert loaded.result=={"answer":42}

def test_handler_failure_requeues_without_nameerror():
    with tempfile.TemporaryDirectory() as td:
        q=AutonomousTaskQueue(Path(td)/"task_queue")
        d=AutonomousTaskDispatcher(q)
        def boom(task):
            raise ValueError("intentional-v39")
        d.register(task_type="research",agent_name="r",handler=boom)
        t=q.enqueue(task_type="research",payload={},idempotency_key="v39-bad",max_attempts=2)
        r=d.dispatch_task(t)
        assert r.dispatched is True
        assert r.reason=="handler_failed"
        loaded=q.load(t.task_id)
        assert loaded.state=="QUEUED"
        assert "intentional-v39" in (loaded.last_error or "")
        assert "result" not in (loaded.last_error or "").lower()

def test_failure_exhausts_cleanly():
    with tempfile.TemporaryDirectory() as td:
        q=AutonomousTaskQueue(Path(td)/"task_queue")
        d=AutonomousTaskDispatcher(q)
        def boom(task):
            raise RuntimeError("boom")
        d.register(task_type="build",agent_name="b",handler=boom)
        t=q.enqueue(task_type="build",payload={},idempotency_key="v39-exhaust",max_attempts=1)
        r=d.dispatch_task(t)
        assert r.reason=="handler_failed"
        assert q.load(t.task_id).state=="FAILED"
PY

echo "===== TESTS ====="
python -m pytest -q   tests/test_v34_worker_lease_store.py   tests/test_v35_lease_execution_guard.py   tests/test_v36_live_recovery_qualification.py   tests/test_v39_dispatch_result_repair.py
echo "TESTS=PASS"

python - <<'PY'
from pathlib import Path
import ast
s=Path("companyos/runtime/autonomous_task_dispatcher.py").read_text()
ast.parse(s)
assert "V39_CLEAN_FENCED_DISPATCH" in s
assert "ok, result, error = guard.execute" in s
assert "self.queue.complete(task, result)" in s
print("RESULT_BINDING_CONTRACT=PASS")
PY

echo "===== CONTROLLED CONTINUOUS CHILD RELOAD ====="
SUP="$(pgrep -f 'companyos/runtime/service_supervisor.py' | head -1 || true)"
[ -n "$SUP" ] || { echo "ABORT=no_supervisor"; exit 30; }
OLD="$(pgrep -f 'companyos.runtime.continuous_goal_runtime|companyos/runtime/continuous_goal_runtime.py' | head -1 || true)"
echo "SUPERVISOR_PID=$SUP OLD_CONTINUOUS=${OLD:-none}"
if [ -n "$OLD" ]; then kill -TERM "$OLD" || true; fi
NEW=""
for i in $(seq 1 30); do
  sleep 1
  NEW="$(pgrep -f 'companyos.runtime.continuous_goal_runtime|companyos/runtime/continuous_goal_runtime.py' | head -1 || true)"
  if [ -n "$NEW" ] && [ "$NEW" != "$OLD" ]; then break; fi
done
[ -n "$NEW" ] || { echo "RELOAD_FAIL=no_continuous_child"; exit 31; }
echo "NEW_CONTINUOUS=$NEW"
echo "RELOAD=PASS"

echo "===== 45 SECOND LIVE FAILURE CHECK ====="
python - <<'PY'
import json,time,collections
from pathlib import Path
q=Path.home()/".companyos_runtime"/"task_queue"
def snap():
    c=collections.Counter()
    for p in q.glob("*.json"):
        try:
            c[str(json.loads(p.read_text()).get("state","UNKNOWN")).upper()]+=1
        except Exception:
            c["UNREADABLE"]+=1
    return c
a=snap(); print("T+000",dict(a),flush=True); b=a
for sec in (15,30,45):
    time.sleep(15); b=snap()
    print(f"T+{sec:03d}",dict(b),
          "completed_delta=",b["COMPLETED"]-a["COMPLETED"],
          "failed_delta=",b["FAILED"]-a["FAILED"],
          "queued_delta=",b["QUEUED"]-a["QUEUED"],flush=True)
print("FINAL_COMPLETED_DELTA=",b["COMPLETED"]-a["COMPLETED"])
print("FINAL_FAILED_DELTA=",b["FAILED"]-a["FAILED"])
print("FINAL_QUEUED_DELTA=",b["QUEUED"]-a["QUEUED"])
PY

git add "$D" tests/test_v39_dispatch_result_repair.py
git diff --cached --quiet || git commit -m "V39 repair fenced dispatcher result binding"
echo "===== V39 COMPLETE ====="
echo "QUEUE_RECORDS_DELETED=0"
echo "FINANCE_CONNECTORS_CHANGED=NO"
echo "SUPERVISOR_RESTARTED=NO"
echo "BACKUP=$B"
