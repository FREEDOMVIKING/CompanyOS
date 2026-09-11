#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase481_496 import (
    MissionState, MissionQueue, EvidenceGate, ValidationMetricsStore,
    OperationsMetricsStore, GateResolver, MissionScheduler,
    PersistentScheduler, SchedulerRuntime
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase496_verify_"))

state = MissionState("m1","research")
assert state.to_dict()["status"] == "queued"

queue = MissionQueue(root)
queue.save([
    {"mission_id":"m1","mission_type":"portfolio","priority":0.9,"attempts":0,"blocked_on":[],"context":{"ventures":[]}},
    {"mission_id":"m2","mission_type":"research","priority":0.5,"attempts":0,"blocked_on":["external_dependency"],"context":{}},
])
assert len(queue.load()) == 2

vg = EvidenceGate().evaluate("validation", {
    "landing_page_visits":100,
    "qualified_leads":5,
})
assert vg["ready"] is True

ValidationMetricsStore(root).put("opp1", {"landing_page_visits":100,"qualified_leads":5})
OperationsMetricsStore(root).put("v1", {"qualified_visitors":100,"leads":10,"sample_size":20})
assert GateResolver(root).resolve_validation("opp1")["gate"]["ready"] is True
assert GateResolver(root).resolve_operations("v1")["gate"]["ready"] is True

ordered = MissionScheduler().order(queue.load())
assert ordered["ready"][0]["mission_id"] == "m1"
assert len(ordered["blocked"]) == 1

result = PersistentScheduler(root).run_once(max_missions=1)
assert result["executed_count"] == 1
assert result["remaining_count"] == 1

assert SchedulerRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase481_496_verification_passed",
    "cycle_status":"phase496_evidence_gate_scheduler_ready",
    "persistent_mission_queue":True,
    "validation_metrics_store":True,
    "operations_metrics_store":True,
    "evidence_gate_resolution":True,
    "mission_priority_scheduler":True,
    "research_validation_venture_build_ops_portfolio_missions":True,
    "autonomy_mode":"high"
}, indent=2))
