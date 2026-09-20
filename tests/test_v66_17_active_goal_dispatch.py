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
