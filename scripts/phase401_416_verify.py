#!/usr/bin/env python3
import json
from companyos_phase401_416 import (
    VentureIntake, ProductBrief, MVPScope, ArchitecturePlan, SpecialistTeam,
    TaskGraph, MilestonePlanner, BuildBudget, QualityGates, ReleasePlan,
    KPIContract, VentureOrchestrator, CEOVentureBridge, VentureRuntime
)

thesis = {
    "name":"Test Venture",
    "customer":"small businesses",
    "core_problem":"manual work is slow",
    "business_model":{"primary":"SaaS"},
}
validation = {"decision":{"decision":"go_to_mvp","confidence":1.0}}

assert VentureIntake().accept(validation)["accepted"] is True
brief = ProductBrief().build(thesis)
assert brief["stage"] == "mvp"
assert MVPScope().define(brief)["scope_rule"]
assert ArchitecturePlan().build(brief)["interfaces"]
assert SpecialistTeam().assign(brief)
assert TaskGraph().create()
assert MilestonePlanner().build()
assert BuildBudget().limits()["max_build_cycles"] >= 1
assert "targeted_tests_pass" in QualityGates().gates()
assert ReleasePlan().build()["rollback_required"] is True
assert KPIContract().build()["activation"]
packet = VentureOrchestrator().prepare(thesis, validation)
assert packet["success"] is True
assert packet["venture_id"].startswith("venture_")
assert CEOVentureBridge().create_venture(thesis, validation)["portfolio_state"] == "incubating"
assert VentureRuntime().status()["success"] is True

rejected = VentureOrchestrator().prepare(thesis, {"decision":{"decision":"no_go_or_pivot"}})
assert rejected["success"] is False

print(json.dumps({
    "success":True,
    "status":"phase401_416_verification_passed",
    "cycle_status":"phase416_venture_factory_ready",
    "validation_gate_required":True,
    "mvp_scope_control":True,
    "specialist_agent_team":True,
    "dependency_task_graph":True,
    "milestone_planning":True,
    "quality_gates":True,
    "release_planning":True,
    "kpi_contracts":True,
    "ceo_venture_bridge":True,
    "autonomy_mode":"high"
}, indent=2))
