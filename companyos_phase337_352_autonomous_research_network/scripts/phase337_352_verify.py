#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase337_352 import (
    StarterResearchNetwork, SourcePolicy, FallbackManager, FreshnessFilter,
    ResearchQualityGate, ProblemClusterer, MarketGapDetector,
    CompetitorPressure, EvidenceOpportunityBuilder, OpportunityConfidence,
    ValidationRouter, CEODecisionInput, ResearchScheduler,
    ResearchNetworkHealth, ResearchNetworkRuntime
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase352_verify_"))
starter = StarterResearchNetwork(root)
assert starter.install_if_missing()["installed"] is True
assert starter.path.exists()

source = {"name":"x","url":"https://example.invalid","enabled":True,"priority":0.9,"category":"pain"}
assert SourcePolicy().evaluate(source)["preferred"] is True
assert FallbackManager().choose([source])[0]["name"] == "x"

records = [{
    "source":"x","title":"Manual reporting is slow",
    "text":"Customers struggle with slow manual reporting and expensive tools.",
    "url":"https://x"
}]
assert FreshnessFilter().filter(records)
quality = ResearchQualityGate(min_score=1).apply(records)
assert quality["accepted"]

problems = [{"statement":"Manual reporting is slow and expensive","source":"x","url":"u"}]
clusters = ProblemClusterer().cluster(problems)
assert clusters
gaps = MarketGapDetector().detect(clusters, [])
assert gaps

opps = EvidenceOpportunityBuilder().build(gaps, clusters)
assert opps
assert OpportunityConfidence().score(opps[0], 2) > 0

routed = ValidationRouter().route([{
    "valid":True,"score":8.0,"opportunity":{"name":"x"},"validation_plan":{}
}])
assert routed[0]["next_action"] == "priority_validation"

packet = CEODecisionInput().build(routed, {"healthy":True})
assert packet["recommended_candidates"]

assert ResearchScheduler().cadence()["interval_minutes"] >= 15
assert ResearchNetworkHealth().summarize([source], {"records":[{}],"errors":[]})["healthy"] is True
assert ResearchNetworkRuntime().status()["success"] is True

print(json.dumps({
    "success": True,
    "status": "phase337_352_verification_passed",
    "cycle_status": "phase352_autonomous_research_network_ready",
    "starter_network": True,
    "fallback_management": True,
    "freshness_filtering": True,
    "quality_gating": True,
    "problem_clustering": True,
    "market_gap_detection": True,
    "confidence_scoring": True,
    "validation_routing": True,
    "ceo_decision_input": True,
    "autonomy_mode": "high"
}, indent=2))
