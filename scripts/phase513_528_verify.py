#!/usr/bin/env python3
import json
from companyos_phase513_528 import (
    RelevanceFilter, SemanticDeduper, EvidenceScorer, CommercialIntent,
    PainSignal, MarketPlausibility, CompetitorSignal, CrossSignalSynthesizer,
    OpportunityQualityPipeline, OpportunityDecisionBrain, QualityRuntime
)

records = [
    {
        "source":"GitHub Issues",
        "title":"Manual contractor estimating workflow is slow",
        "text":"Contractors spend hours on manual estimates and existing software is expensive.",
        "url":"https://example.test/1",
        "metadata":{"comments":5}
    },
    {
        "source":"Hacker News",
        "title":"Small contractors want simpler proposal software",
        "text":"Business owners complain current proposal software pricing is expensive and workflows are manual.",
        "url":"https://example.test/2",
        "metadata":{"comments":20}
    },
    {
        "source":"News",
        "title":"Ancient tomb painting discovered",
        "text":"Archaeology story unrelated to software or business workflows.",
        "url":"https://example.test/3"
    }
]

rf = RelevanceFilter().apply(records)
assert len(rf["accepted"]) >= 2
assert SemanticDeduper().unique(rf["accepted"])
assert EvidenceScorer().score(records[0]) > 0
assert CommercialIntent().score(records[0]) > 0
assert PainSignal().score(records[0]) > 0
assert MarketPlausibility().score(records[0]) > 0
assert CompetitorSignal().analyze(records[0])["has_competitive_market"] is True
assert CrossSignalSynthesizer().synthesize(rf["accepted"])

result = OpportunityQualityPipeline().run(records)
assert result["success"] is True
assert result["candidates"]
assert result["records_rejected"] >= 1
assert result["top_candidate"]["decision"]["decision"] in ("priority_validate","validate","research_more","reject")

assert OpportunityDecisionBrain().evaluate({
    "quality_score":2,"evidence_count":1,"source_count":1,"dimensions":{}
})["decision"] == "reject"

assert QualityRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase513_528_verification_passed",
    "cycle_status":"phase528_opportunity_quality_decision_brain_ready",
    "relevance_filtering":True,
    "semantic_deduplication":True,
    "evidence_scoring":True,
    "commercial_intent":True,
    "pain_scoring":True,
    "market_plausibility":True,
    "cross_signal_synthesis":True,
    "junk_rejection":True,
    "autonomous_decision_policy":True,
    "autonomy_mode":"high"
}, indent=2))
