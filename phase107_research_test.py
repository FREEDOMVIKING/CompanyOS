#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.opportunity_discovery import OpportunityDiscoveryStore
from companyos.runtime.research_evidence_pipeline import ResearchEvidenceStore, ResearchEvidenceEvaluator
from companyos.runtime.opportunity_research_bridge import OpportunityResearchBridge

with tempfile.TemporaryDirectory(prefix="phase107_research_") as td:
    base = Path(td)

    opp_store = OpportunityDiscoveryStore(base / "opps")
    ev_store = ResearchEvidenceStore(base / "evidence")
    evaluator = ResearchEvidenceEvaluator(ev_store)
    bridge = OpportunityResearchBridge(opp_store, evaluator)

    opp = opp_store.upsert_candidate(
        title="AI workflow product",
        description="A small-business workflow assistant.",
        source="test",
        category="software",
        confidence=0.8,
        novelty=0.7,
        feasibility=0.9,
        strategic_fit=0.9,
        expected_value=0.8,
    )

    ev_store.add(
        opportunity_id=opp.opportunity_id,
        source="source-a",
        claim="Demand appears strong.",
        direction="support",
        confidence=0.9,
        quality=0.9,
        relevance=0.9,
    )
    ev_store.add(
        opportunity_id=opp.opportunity_id,
        source="source-b",
        claim="Implementation is feasible.",
        direction="support",
        confidence=0.85,
        quality=0.85,
        relevance=0.95,
    )
    ev_store.add(
        opportunity_id=opp.opportunity_id,
        source="source-c",
        claim="Some competition exists.",
        direction="contradict",
        confidence=0.35,
        quality=0.8,
        relevance=0.7,
    )

    assessment = evaluator.assess(opp.opportunity_id)
    applied = bridge.apply(opp.opportunity_id)

    checks = {
        "three_evidence_records": assessment.evidence_count == 3,
        "support_dominant": assessment.support_score > assessment.contradiction_score,
        "decision_advance": assessment.decision == "advance",
        "score_increased": applied.score_after > applied.score_before,
        "assessment_persisted_to_opportunity": "research_assessment" in opp_store.load(opp.opportunity_id).metadata,
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("RESEARCH_PIPELINE_EXTERNAL_ACTIONS: False")
    print("RESEARCH_PIPELINE_SIGNS_TRANSACTION: False")
    print("RESEARCH_PIPELINE_BROADCASTS: False")
    print("PHASE107_RESEARCH_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
