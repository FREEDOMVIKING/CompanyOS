#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase497_512 import (
    ObjectiveStore, MissionGenerator, DependencyResolver, EventStore,
    EventRouter, MissionDeduper, MissionBudget, MissionReprioritizer,
    SchedulerHeartbeat, StalledWorkDetector, ResumeEngine, SchedulerState,
    MissionAudit, AutonomousSchedulerRuntime
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase512_verify_"))

assert ObjectiveStore(root).load()["primary"]

missions = MissionGenerator().generate(
    {"current_stage":"validation"},
    {"top_thesis":{"name":"X"}}
)
assert missions and missions[0]["blocked_on"] == ["validation_evidence"]

resolved = DependencyResolver().resolve(
    missions[0],
    {"validation_metrics":{"landing_page_visits":100}}
)
assert "validation_evidence" not in resolved["mission"]["blocked_on"]

assert EventStore(root).append("x")["event_type"] == "x"
assert EventRouter().route("new_evidence") == "reprioritize"
assert len(MissionDeduper().unique(missions + missions)) == 1
assert MissionBudget().limits()["max_execute_per_tick"] >= 1
assert MissionReprioritizer().apply(missions)
assert SchedulerHeartbeat().beat(1,0)["alive"] is True
assert StalledWorkDetector().detect([{"attempts":3,"status":"queued"}])
assert ResumeEngine().resume(missions, {"validation_metrics":{"x":1}})["resumed"]
state = SchedulerState(root)
state.save({"ticks":1})
assert state.load()["ticks"] == 1
assert MissionAudit(root).record({"mission_id":"m","mission_type":"x"},{"success":True})
assert AutonomousSchedulerRuntime().status()["success"] is True

print(json.dumps({
    "success": True,
    "status": "phase497_512_verification_passed",
    "cycle_status": "phase512_autonomous_ceo_scheduler_ready",
    "objective_store": True,
    "mission_generation": True,
    "dependency_resolution": True,
    "event_stream": True,
    "mission_deduplication": True,
    "mission_budgets": True,
    "dynamic_reprioritization": True,
    "heartbeat": True,
    "stalled_work_detection": True,
    "resume_engine": True,
    "autonomy_mode": "high"
}, indent=2))
