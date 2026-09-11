from pathlib import Path
import tempfile
from companyos.daemonops import DurableJobQueue
from companyos.workerops import DurableWorkerPool, BackpressureController, WorkerRouter

def test_worker_drain():
    root=Path(tempfile.mkdtemp())
    q=DurableJobQueue(root)
    q.enqueue("research",{},5)
    r=DurableWorkerPool(root).process_one(q,tick=1)
    assert r["processed"]
    assert q.load()[0]["status"]=="complete"

def test_backpressure():
    assert BackpressureController().evaluate(120)["mode"]=="hard"

def test_router():
    assert WorkerRouter().route({"kind":"finance","payload":{}})=="finance"
