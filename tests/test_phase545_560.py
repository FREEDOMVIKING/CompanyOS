from datetime import datetime, timezone
from companyos_phase545_560 import BackoffPolicy, CrashRecovery, CEOWatchdog

def test_backoff():
    assert BackoffPolicy().delay(3) > BackoffPolicy().delay(1)

def test_recovery():
    assert CrashRecovery().decide(1,5)["action"] == "backoff_and_retry"
    assert CrashRecovery().decide(5,5)["action"] == "halt_for_review"

def test_watchdog():
    state = {
        "last_tick_at":datetime.now(timezone.utc).isoformat(),
        "consecutive_failures":0,
    }
    assert CEOWatchdog().evaluate(state,900)["healthy"] is True
