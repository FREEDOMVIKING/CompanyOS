from companyos.runtime import PersistentJobQueue, RuntimeWatchdog, RestartSafeRecovery
from datetime import datetime, timezone

def test_queue(tmp_path):
    q=PersistentJobQueue(tmp_path)
    q.enqueue("x",{},5)
    assert q.snapshot()["queued"]==1

def test_watchdog():
    hb={"timestamp":datetime.now(timezone.utc).isoformat()}
    assert RuntimeWatchdog().evaluate(hb)["healthy"] is True

def test_recovery():
    assert RestartSafeRecovery().recover({"state":{"x":1}},{"running":0})["recoverable"] is True
