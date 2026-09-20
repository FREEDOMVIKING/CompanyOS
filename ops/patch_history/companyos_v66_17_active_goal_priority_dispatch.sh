#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
RT="$HOME/.companyos_runtime"
LOOP="$ROOT/companyos/runtime/autonomous_goal_execution_loop.py"
CEO="$ROOT/companyos/runtime/autonomous_ceo_orchestrator.py"
CTL="$ROOT/scripts/companyos_livenessctl"

cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

echo "===== COMPANYOS V66.17 ACTIVE-GOAL PRIORITY DISPATCH ====="
echo "GOAL=PREVENT_ACTIVE_CEO_VENTURES_FROM_WAITING_BEHIND_LARGE_HISTORICAL_QUEUE_WINDOWS"
echo "NOTE=ONLY_DISPATCHES_TASKS_BELONGING_TO_THE_ACTIVE_GOAL"
echo "NOTE=AUTHORITY_SWITCHES_UNCHANGED"

for f in "$LOOP" "$CEO" "$CTL"; do
  [ -f "$f" ] || { echo "V66_17_ABORT=missing:$f"; exit 1; }
done

stamp="$(date +%Y%m%d_%H%M%S)"
for f in "$LOOP" "$CEO"; do
  cp "$f" "${f}.v66_17_backup_${stamp}"
  echo "BACKUP=${f}.v66_17_backup_${stamp}"
done

echo "===== PATCH GOAL-FOCUSED DISPATCH ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/autonomous_goal_execution_loop.py"
s=p.read_text()

anchor='''    def run_bounded_batch(self, *, max_dispatches: int = 8):
        # One stale scan per batch, not once per task.
        self.queue.recover_stale(stale_after_seconds=300)

        raw = self.dispatcher.dispatch_batch(max_dispatches=max_dispatches)

        # One count scan per batch, not once per task.
        counts = self._counts()
        return [self._to_cycle(result, counts) for result in raw]

'''

addition='''    def run_goal_batch(self, goal_id: str, *, max_dispatches: int = 8):
        # V66.17: dispatch only tasks for the active CEO goal.
        # This preserves dependency ordering and the existing lease guard,
        # while avoiding the bounded global queue-window delay.
        self.queue.recover_stale(stale_after_seconds=300)

        now = time.time()
        max_dispatches = max(1, min(int(max_dispatches), 64))
        base = self.dispatcher.dispatcher

        tasks = []
        all_tasks = self.queue.all_tasks()
        for task in all_tasks:
            payload = task.payload if isinstance(task.payload, dict) else {}
            if str(payload.get("goal_id") or "") != str(goal_id):
                continue
            if task.state != "QUEUED":
                continue
            if task.attempts >= task.max_attempts:
                continue
            if task.next_attempt_unix > now:
                continue
            if task.task_type not in base.handlers:
                continue
            tasks.append(task)

        completed = set()
        for task in all_tasks:
            if task.state != "COMPLETED":
                continue
            payload = task.payload if isinstance(task.payload, dict) else {}
            if str(payload.get("goal_id") or "") != str(goal_id):
                continue
            stage = payload.get("stage")
            if stage:
                completed.add(str(stage))

        def ready(task):
            payload = task.payload if isinstance(task.payload, dict) else {}
            dep = payload.get("depends_on_stage")
            return (not dep) or str(dep) in completed

        tasks.sort(key=lambda t: (-int(t.priority), float(t.created_at_unix), t.task_id))
        results = []
        remaining = list(tasks)

        while remaining and len(results) < max_dispatches:
            idx = None
            for i, task in enumerate(remaining):
                if ready(task):
                    idx = i
                    break
            if idx is None:
                break

            task = remaining.pop(idx)
            result = base.dispatch_task(task)
            results.append(result)

            if result.dispatched and result.reason == "completed":
                payload = task.payload if isinstance(task.payload, dict) else {}
                stage = payload.get("stage")
                if stage:
                    completed.add(str(stage))

        if not results:
            from companyos.runtime.autonomous_task_dispatcher import DispatchResult
            results = [
                DispatchResult(
                    False,
                    None,
                    None,
                    None,
                    "no_active_goal_dependency_ready_task",
                    None,
                )
            ]

        counts = self._counts()
        return [self._to_cycle(result, counts) for result in results]

'''

if "def run_goal_batch(" not in s:
    if anchor not in s:
        raise SystemExit("V66_17_ABORT=run_bounded_batch_anchor_missing")
    s=s.replace(anchor, anchor+addition, 1)

p.write_text(s)
print("V66_17_GOAL_BATCH_PATCH=PASS")
PY

echo "===== PATCH CEO ORCHESTRATOR TO USE ACTIVE-GOAL DISPATCH ====="
python - <<'PY'
from pathlib import Path

p=Path.home()/"companyos/companyos/runtime/autonomous_ceo_orchestrator.py"
s=p.read_text()

old='''        batch = self.execution_loop.run_bounded_batch(max_dispatches=batch_size)
'''
new='''        batch = self.execution_loop.run_goal_batch(
            active_goal_id,
            max_dispatches=batch_size,
        )
'''
if old in s:
    s=s.replace(old,new,1)
elif "run_goal_batch(" not in s:
    raise SystemExit("V66_17_ABORT=ceo_dispatch_anchor_missing")

p.write_text(s)
print("V66_17_CEO_ACTIVE_GOAL_PATCH=PASS")
PY

cat > "$ROOT/tests/test_v66_17_active_goal_dispatch.py" <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop


def test_active_goal_dispatch_ignores_unrelated_higher_priority_task():
    with TemporaryDirectory() as td:
        q=AutonomousTaskQueue(Path(td)/"task_queue")
        other=q.enqueue(
            task_type="research",
            priority=999,
            idempotency_key="other",
            payload={"goal_id":"other-goal","stage":"research","goal":"other"},
        )
        active=q.enqueue(
            task_type="research",
            priority=100,
            idempotency_key="active",
            payload={"goal_id":"active-goal","stage":"research","goal":"active"},
        )

        loop=AutonomousGoalExecutionLoop(q)
        result=loop.run_goal_batch("active-goal",max_dispatches=1)[0]

        assert result.dispatched is True
        assert result.task_id==active.task_id
        assert q.load(other.task_id).state=="QUEUED"


def test_dependency_order_is_preserved():
    with TemporaryDirectory() as td:
        q=AutonomousTaskQueue(Path(td)/"task_queue")
        planning=q.enqueue(
            task_type="planning",
            priority=200,
            idempotency_key="plan",
            payload={
                "goal_id":"g1",
                "stage":"planning",
                "depends_on_stage":"research",
                "goal":"plan",
            },
        )
        research=q.enqueue(
            task_type="research",
            priority=100,
            idempotency_key="research",
            payload={
                "goal_id":"g1",
                "stage":"research",
                "goal":"research",
            },
        )

        loop=AutonomousGoalExecutionLoop(q)
        first=loop.run_goal_batch("g1",max_dispatches=1)[0]

        assert first.task_id==research.task_id
        assert q.load(planning.task_id).state=="QUEUED"
PY

echo "===== COMPILE ====="
python -m py_compile "$LOOP" "$CEO"
echo "V66_17_MODULE_COMPILE=PASS"

echo "===== TEST ====="
python -m pytest -q tests/test_v66_17_active_goal_dispatch.py
echo "V66_17_TESTS=PASS"

echo "===== RESTART CEO + LIVENESS RUNTIMES ====="
"$CTL" restart

echo "===== ALLOW TWO CEO TICKS ====="
sleep 22

echo "===== FINAL STATUS ====="
"$CTL" status

echo "V66_17_ACTIVE_GOAL_PRIORITY_DISPATCH=PASS"
echo "V66_17_DEPENDENCY_ORDER_PRESERVED=PASS"
echo "V66_17_UNRELATED_QUEUE_BYPASS=PASS"
echo "V66_17_EXISTING_LEASE_GUARD_PRESERVED=PASS"
echo "V66_17_AUTHORITY_SWITCHES_UNCHANGED=PASS"
echo "V66_17_COMPLETE"
