from companyos_phase277_284 import RunLock, FailureTracker, CycleBudget

def test_lock(tmp_path):
    lock = RunLock(tmp_path)
    assert lock.acquire()["acquired"] is True
    assert lock.acquire()["acquired"] is False
    lock.release()

def test_failure_tracker(tmp_path):
    tracker = FailureTracker(tmp_path)
    assert tracker.record(False)["consecutive_failures"] == 1
    assert tracker.record(True)["consecutive_failures"] == 0

def test_budget():
    assert CycleBudget().limits()["max_cycles_per_run"] >= 1
