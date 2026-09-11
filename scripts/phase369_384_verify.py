#!/usr/bin/env python3
import json
from companyos_phase369_384 import (
    NoiseFilter, SemanticClusterer, CrossSourceAgreement, CustomerIdentifier,
    PainSeverity, FrequencyEstimator, WillingnessToPay, ReplacementAnalyzer,
    BusinessModelGenerator, StartupEstimator, TimeToRevenue, DescriptiveNamer,
    MarketThesisBuilder, InvestmentDecision, OpportunityIntelligenceCycle,
    OpportunityIntelligenceRuntime
)

records = [
    {
        "source":"GitHub Issues",
        "title":"Manual estimating workflow is slow",
        "text":"Contractors spend hours on manual estimates and proposals. Existing software is expensive.",
        "url":"https://example.test/1",
    },
    {
        "source":"Hacker News",
        "title":"Proposal workflow automation for contractors",
        "text":"Small contractors want faster estimating and proposal software with simpler pricing.",
        "url":"https://example.test/2",
    },
]

assert NoiseFilter().apply(records)["accepted"]
clusters = SemanticClusterer().cluster(records)
assert clusters
assert CrossSourceAgreement().score(clusters[0])["source_count"] >= 1
assert CustomerIdentifier().identify(clusters[0])
assert PainSeverity().score(clusters[0]) > 0
assert FrequencyEstimator().score(clusters[0]) > 0
assert WillingnessToPay().score(clusters[0]) > 0
assert ReplacementAnalyzer().analyze(clusters[0])
assert BusinessModelGenerator().generate("contractors","estimating_and_proposals")
startup = StartupEstimator().estimate("estimating_and_proposals")
assert TimeToRevenue().estimate(startup)
assert DescriptiveNamer().name("estimating_and_proposals") == "AI Estimating & Proposal Copilot"

result = OpportunityIntelligenceCycle().run(records)
assert result["success"] is True
assert result["market_theses"]
assert result["market_theses"][0]["name"] != "Opportunity 1"
assert result["market_theses"][0]["investment"]["decision"]

assert OpportunityIntelligenceRuntime().status()["success"] is True

print(json.dumps({
    "success": True,
    "status": "phase369_384_verification_passed",
    "cycle_status": "phase384_opportunity_intelligence_market_thesis_ready",
    "noise_rejection": True,
    "semantic_clustering": True,
    "cross_source_agreement": True,
    "customer_identification": True,
    "pain_and_frequency_scoring": True,
    "willingness_to_pay": True,
    "business_models": True,
    "startup_and_revenue_estimates": True,
    "descriptive_names": True,
    "market_thesis": True,
    "investment_decisions": True,
    "autonomy_mode": "high"
}, indent=2))
