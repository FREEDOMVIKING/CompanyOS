#!/usr/bin/env python3
import json
from companyos_phase417_432 import (
    VentureBuildIntake, SpecialistDispatcher, BuildCycle, TestRepairLoop,
    ReleaseCandidate, MetricInstrumentation, PortfolioDecision,
    AutonomousBuildBridge, VentureExecutionRuntime
)

packet = {
    "success":True,
    "venture_id":"venture_test",
    "brief":{"product_name":"Test"},
    "mvp_scope":{"must_have":["core"]},
    "architecture":{"interfaces":["ui"]},
    "task_graph":[
        {"id":"T1","task":"finalize product brief","depends_on":[]},
        {"id":"T2","task":"define architecture and interfaces","depends_on":["T1"]},
        {"id":"T3","task":"implement core value loop","depends_on":["T2"]},
        {"id":"T4","task":"run quality gates","depends_on":["T3"]},
    ],
    "quality_gates":["targeted_tests_pass","regression_tests_pass"],
    "kpis":{"activation":["activation_rate"],"retention":["return_rate"]},
    "build_budget":{"max_build_cycles":8,"max_repair_cycles":4},
}

assert VentureBuildIntake().accept(packet)["accepted"] is True
jobs = SpecialistDispatcher().dispatch(packet["task_graph"])
assert len(jobs) == 4
state = BuildCycle().start(packet)
assert state["max_cycles"] == 8
assert TestRepairLoop().evaluate({"passed":False},0,4)["action"] == "repair"
assert TestRepairLoop().evaluate({"passed":True},0,4)["action"] == "promote"
rc = ReleaseCandidate().evaluate(
    {"required":packet["quality_gates"],"passed":packet["quality_gates"]},
    ["app.py"]
)
assert rc["release_candidate_ready"] is True
assert rc["external_launch_authorized"] is False
metrics = MetricInstrumentation().plan(packet["kpis"])
assert metrics["event_count"] == 2
assert PortfolioDecision().decide({"sample_size":5})["decision"] == "hold_for_more_evidence"
bridge = AutonomousBuildBridge().prepare_build(packet)
assert bridge["success"] is True
assert bridge["builder_contract"]["external_launch"] is False
assert VentureExecutionRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase417_432_verification_passed",
    "cycle_status":"phase432_autonomous_build_bridge_ready",
    "venture_factory_connected":True,
    "specialist_dispatch":True,
    "bounded_build_cycles":True,
    "test_repair_loop":True,
    "release_candidate_gate":True,
    "kpi_feedback_loop":True,
    "autonomy_mode":"high"
}, indent=2))
