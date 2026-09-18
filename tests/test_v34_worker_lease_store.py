import multiprocessing as mp
import tempfile
from pathlib import Path

from companyos.runtime.durable_execution_kernel import DurableExecutionKernel
from companyos.runtime.worker_lease_store import WorkerLeaseStore


def _kernel(td):
    return DurableExecutionKernel(Path(td))


def _race_claim(db_path, task_id, owner, queue):
    store = WorkerLeaseStore(Path(db_path))
    lease = store.claim(task_id, owner, ttl=30, now=100)
    queue.put(bool(lease))


def test_six_workers_only_one_claims():
    with tempfile.TemporaryDirectory() as td:
        kernel = _kernel(td)
        store = WorkerLeaseStore(kernel.db_path)
        queue = mp.Queue()
        workers = [
            mp.Process(
                target=_race_claim,
                args=(str(kernel.db_path), "race-task", f"worker-{i}", queue),
            )
            for i in range(6)
        ]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(15)
        assert all(not worker.is_alive() for worker in workers)
        results = [queue.get(timeout=3) for _ in workers]
        assert sum(results) == 1
        assert store.active_count(now=101) == 1


def test_expired_worker_is_recoverable():
    with tempfile.TemporaryDirectory() as td:
        kernel = _kernel(td)
        store = WorkerLeaseStore(kernel.db_path)
        first = store.claim("crash-task", "dead-worker", ttl=5, now=100)
        assert first is not None
        assert store.claim("crash-task", "blocked-worker", ttl=5, now=103) is None
        recovered = store.claim("crash-task", "recovery-worker", ttl=5, now=106)
        assert recovered is not None
        assert recovered.owner == "recovery-worker"


def test_fencing_blocks_old_worker_release():
    with tempfile.TemporaryDirectory() as td:
        kernel = _kernel(td)
        store = WorkerLeaseStore(kernel.db_path)
        old = store.claim("fenced-task", "old-worker", ttl=2, now=100)
        assert old is not None
        new = store.claim("fenced-task", "new-worker", ttl=20, now=103)
        assert new is not None
        assert store.release(old) is False
        assert store.active_count(now=104) == 1


def test_heartbeat_extends_lease():
    with tempfile.TemporaryDirectory() as td:
        kernel = _kernel(td)
        store = WorkerLeaseStore(kernel.db_path)
        lease = store.claim("heartbeat-task", "worker", ttl=5, now=100)
        assert lease is not None
        assert store.heartbeat(lease, ttl=10, now=103) is True
        assert store.active_count(now=110) == 1
        assert store.recover_expired(now=114) == 1


def test_release_requires_matching_fence_token():
    with tempfile.TemporaryDirectory() as td:
        kernel = _kernel(td)
        store = WorkerLeaseStore(kernel.db_path)
        lease = store.claim("release-task", "worker", ttl=20, now=100)
        assert lease is not None
        assert store.release(lease) is True
        assert store.active_count(now=101) == 0
