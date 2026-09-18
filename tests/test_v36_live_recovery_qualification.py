import multiprocessing as mp
import tempfile, time
from pathlib import Path
from companyos.runtime.durable_execution_kernel import DurableExecutionKernel
from companyos.runtime.worker_lease_store import WorkerLeaseStore
from companyos.runtime.lease_execution_guard import LeaseExecutionGuard

def holder(db, ready):
    s=WorkerLeaseStore(Path(db))
    lease=s.claim("v36-crash-task","crash-worker",ttl=1.0)
    assert lease is not None
    ready.set()
    while True:
        s.heartbeat(lease,ttl=1.0)
        time.sleep(.15)

def test_crashed_owner_expires_and_reclaims():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d))
        ready=mp.Event()
        p=mp.Process(target=holder,args=(str(k.db_path),ready))
        p.start()
        assert ready.wait(3)
        s=WorkerLeaseStore(k.db_path)
        assert s.claim("v36-crash-task","competitor",ttl=1.0) is None
        p.terminate(); p.join(3)
        time.sleep(1.25)
        lease=s.claim("v36-crash-task","recovery-worker",ttl=2.0)
        assert lease is not None
        s.release(lease)

def test_guard_prevents_parallel_duplicate():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d))
        g=LeaseExecutionGuard(k.db_path)
        held=g.store.claim("v36-dup","owner-a",ttl=5)
        assert held is not None
        ok,val,err=g.execute("v36-dup","owner-b",lambda: 99,ttl=2,interval=.2)
        assert not ok and val is None and err=="lease_unavailable"
        g.store.release(held)

def test_guard_checkpoint_and_success():
    with tempfile.TemporaryDirectory() as d:
        k=DurableExecutionKernel(Path(d))
        g=LeaseExecutionGuard(k.db_path)
        ok,val,err=g.execute("v36-success","owner",lambda: 42,ttl=2,interval=.2)
        assert ok and val==42 and err is None
