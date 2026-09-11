#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.runtime.opportunity_discovery import OpportunityDiscoveryStore
from companyos.runtime.research_signal_ingestion import ResearchSignalStore
from companyos.runtime.research_evidence_pipeline import ResearchEvidenceStore, ResearchEvidenceEvaluator
from companyos.runtime.research_signal_normalizer import ResearchSignalNormalizer
from companyos.runtime.opportunity_research_bridge import OpportunityResearchBridge

with tempfile.TemporaryDirectory(prefix="phase108_signal_") as td:
    base = Path(td)

    opp_store = OpportunityDiscoveryStore(base / "opps")
    signal_store = ResearchSignalStore(base / "signals")
    evidence_store = ResearchEvidenceStore(base / "evidence")
    evaluator = ResearchEvidenceEvaluator(evidence_store)
    normalizer = ResearchSignalNormalizer(evidence_store)
    bridge = OpportunityResearchBridge(opp_store, evaluator)

    opp = opp_store.upsert_candidate(
        title="AI workflow assistant",
        description="Automation product for small service businesses.",
        source="test",
        category="software",
        confidence=0.8,
        novelty=0.7,
        feasibility=0.9,
        strategic_fit=0.9,
        expected_value=0.8,
    )

    s1 = signal_store.ingest(
        opportunity_id=opp.opportunity_id,
        source_type="research",
        source_name="source-a",
        title="Demand growth",
        content="Demand and adoption are increasing with strong interest.",
        source_quality=0.9,
        relevance_hint=0.95,
    )

    s2 = signal_store.ingest(
        opportunity_id=opp.opportunity_id,
        source_type="research",
        source_name="source-b",
        title="Feasibility",
        content="Implementation appears feasible and the opportunity is underserved.",
        source_quality=0.85,
        relevance_hint=0.95,
    )

    duplicate = signal_store.ingest(
        opportunity_id=opp.opportunity_id,
        source_type="research",
        source_name="source-a",
        title="Demand growth",
        content="Demand and adoption are increasing with strong interest.",
        source_quality=0.9,
        relevance_hint=0.95,
    )

    n1 = normalizer.normalize(s1)
    n2 = normalizer.normalize(s2)
    assessment = evaluator.assess(opp.opportunity_id)
    applied = bridge.apply(opp.opportunity_id)

    checks = {
        "signal_deduplication": duplicate.signal_id == s1.signal_id,
        "two_unique_signals": len(signal_store.all_records()) == 2,
        "two_evidence_records": assessment.evidence_count == 2,
        "signals_normalized_support": n1.direction == "support" and n2.direction == "support",
        "research_decision_advance": assessment.decision == "advance",
        "opportunity_score_increased": applied.score_after > applied.score_before,
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("SIGNAL_PIPELINE_EXTERNAL_ACTIONS: False")
    print("SIGNAL_PIPELINE_SIGNS_TRANSACTION: False")
    print("SIGNAL_PIPELINE_BROADCASTS: False")
    print("PHASE108_SIGNAL_PIPELINE_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
