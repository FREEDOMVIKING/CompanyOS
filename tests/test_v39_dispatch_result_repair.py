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
