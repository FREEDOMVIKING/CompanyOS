#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase529_544 import (
    CandidateRouter, ResearchMoreMission, ValidationCandidateBuilder,
    QualitySchedulerBridge, QualityMissionGenerator, CandidatePriority,
    CandidateDeduper, CandidateState, SchedulerQualityHook,
    DecisionEventRouter, QualityPortfolioMemory, IntegrationHealth,
    IntegrationRuntime
)

candidate = {
    "name":"Workflow Automation",
    "theme":"workflow_automation",
    "quality_score":7.2,
    "source_count":2,
    "evidence_links":["u1","u2"],
    "dimensions":{"pain":6,"commercial_intent":5},
    "decision":{"decision":"validate"},
}

assert CandidateRouter().route(candidate) == "validation"
assert ResearchMoreMission().build({**candidate,"decision":{"decision":"research_more"}})["mission_type"] == "research"
assert ValidationCandidateBuilder().build(candidate)["name"] == "Workflow Automation"
mission = QualitySchedulerBridge().build_mission(candidate)
assert mission["mission_type"] == "validation"
generated = QualityMissionGenerator().generate([candidate])
assert generated and generated[0]["mission_id"].startswith("mission_")
assert CandidatePriority().score(candidate) > 0
assert len(CandidateDeduper().unique([candidate,candidate])) == 1
assert CandidateState("x","y").to_dict()["status"] == "scored"

root = Path(tempfile.mkdtemp(prefix="companyos_phase544_verify_"))
hook = SchedulerQualityHook(root)
assert hook.inject(generated)["queue_size"] == 1
assert hook.inject(generated)["queue_size"] == 1
assert DecisionEventRouter().event_for(candidate) == "quality_candidate_ready_for_validation"
assert QualityPortfolioMemory(root).append(candidate, "x")
assert IntegrationHealth().evaluate({"generated_missions":generated,"candidates":[candidate]})["healthy"] is True
assert IntegrationRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase529_544_verification_passed",
    "cycle_status":"phase544_quality_aware_scheduler_integration_ready",
    "candidate_routing":True,
    "targeted_research_more":True,
    "validation_candidate_builder":True,
    "quality_mission_generation":True,
    "candidate_priority":True,
    "candidate_deduplication":True,
    "scheduler_quality_hook":True,
    "decision_events":True,
    "quality_portfolio_memory":True,
    "autonomy_mode":"high"
}, indent=2))
