import tempfile
from pathlib import Path
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
def test_v33_index():
    with tempfile.TemporaryDirectory() as d:
        q=AutonomousTaskQueue(Path(d)/"task_queue")
        a=q.enqueue(task_type="research",payload={"goal_id":"g","stage":"research"},idempotency_key="x")
        assert q.kernel.idempotent_task("x")==a.task_id
        a=q.mark_running(a); q.complete(a,{"ok":True})
        assert q.kernel.completed_stage("g","research")
def test_v33_idempotency():
    with tempfile.TemporaryDirectory() as d:
        q=AutonomousTaskQueue(Path(d)/"task_queue")
        a=q.enqueue(task_type="build",payload={},idempotency_key="same")
        b=q.enqueue(task_type="build",payload={},idempotency_key="same")
        assert a.task_id==b.task_id
