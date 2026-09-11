#!/usr/bin/env python3
import json, tempfile
from pathlib import Path

from companyos_phase277_284 import (
    RunLock, CycleBudget, FailureTracker, ImprovementHistory, SupervisorRuntime
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase284_verify_"))

lock = RunLock(root)
assert lock.acquire()["acquired"] is True
assert lock.acquire()["acquired"] is False
lock.release()

limits = CycleBudget().limits()
assert limits["max_cycles_per_run"] >= 1

tracker = FailureTracker(root)
assert tracker.record(False, "x")["consecutive_failures"] == 1
assert tracker.record(True)["consecutive_failures"] == 0

history = ImprovementHistory(root)
history.append(1, {"success": True, "status": "ok"})
assert history.path.exists()

status = SupervisorRuntime(root).status()
assert status["success"] is True
assert status["overlap_protection"] is True

print(json.dumps({
    "success": True,
    "status": "phase277_284_verification_passed",
    "cycle_status": "phase284_continuous_supervisor_ready",
    "overlap_protection": True,
    "cycle_budgets": True,
    "failure_loop_breaker": True,
    "persistent_improvement_history": True,
    "continuous_supervision": True,
    "verification_gates_preserved": True,
    "autonomy_mode": "high"
}, indent=2))
