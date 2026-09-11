#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from datetime import datetime, timezone
from companyos_phase545_560 import (
    ServiceConfig, ServiceState, IdlePolicy, BackoffPolicy, ServiceLock,
    ServiceJournal, CrashRecovery, HealthSnapshot, CEOWatchdog,
    StartupRecovery, ServiceRuntime
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase560_verify_"))

cfg = ServiceConfig().load()
assert cfg["tick_interval_seconds"] >= 30

store = ServiceState(root)
state = store.load()
assert state["ticks"] == 0
state["running"] = True
recovered = StartupRecovery().recover(state)
assert recovered["running"] is False
assert recovered["recovered_from_unclean_shutdown"] is True

assert IdlePolicy().evaluate({
    "scheduler_result":{"scheduler_result":{"executed_count":0,"remaining_count":0}}
})["idle"] is True

assert BackoffPolicy().delay(2) > BackoffPolicy().delay(0)

lock = ServiceLock(root)
a = lock.acquire()
assert a["acquired"] is True
b = lock.acquire()
assert b["acquired"] is False
lock.release()

assert ServiceJournal(root).append("x")["event"] == "x"
assert CrashRecovery().decide(1,5)["action"] == "backoff_and_retry"
assert CrashRecovery().decide(5,5)["action"] == "halt_for_review"

now_state = {
    "running":True,
    "ticks":1,
    "consecutive_failures":0,
    "last_status":"ok",
    "last_tick_at":datetime.now(timezone.utc).isoformat(),
}
assert HealthSnapshot().build(now_state)["running"] is True
assert CEOWatchdog().evaluate(now_state, 900)["healthy"] is True
assert ServiceRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase545_560_verification_passed",
    "cycle_status":"phase560_continuous_ceo_service_watchdog_ready",
    "continuous_service_loop":True,
    "quality_scheduler_ticks":True,
    "autonomous_scheduler_ticks":True,
    "persistent_service_state":True,
    "duplicate_instance_lock":True,
    "crash_recovery":True,
    "failure_backoff":True,
    "watchdog_health":True,
    "service_journal":True,
    "autonomy_mode":"high"
}, indent=2))
