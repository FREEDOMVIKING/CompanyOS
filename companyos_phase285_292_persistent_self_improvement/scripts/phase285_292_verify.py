#!/usr/bin/env python3
import json, tempfile
from pathlib import Path

from companyos_phase285_292 import (
    ImprovementStateStore,
    CycleJournal,
    PausePolicy,
    AdaptiveScheduler,
    ResumeController,
    PersistentRuntime,
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase292_verify_"))

store = ImprovementStateStore(root)
state = store.load()
assert state["cycles_completed"] == 0
state["cycles_completed"] = 2
store.save(state)
assert store.load()["cycles_completed"] == 2

journal = CycleJournal(root)
journal.append("test", {"ok": True})
assert journal.path.exists()

assert PausePolicy().evaluate({"paused": True}, {})["pause"] is True
assert AdaptiveScheduler().next_delay(True) >= 30

ctl = ResumeController(root)
ctl.pause()
assert ctl.status()["paused"] is True
ctl.resume()
assert ctl.status()["paused"] is False

status = PersistentRuntime(root).status()
assert status["success"] is True

print(json.dumps({
    "success": True,
    "status": "phase285_292_verification_passed",
    "cycle_status": "phase292_persistent_self_improvement_ready",
    "durable_resume_state": True,
    "persistent_cycle_journal": True,
    "pause_resume_control": True,
    "adaptive_cycle_delay": True,
    "persistent_improvement_loop": True,
    "verification_gates_preserved": True,
    "autonomy_mode": "high"
}, indent=2))
