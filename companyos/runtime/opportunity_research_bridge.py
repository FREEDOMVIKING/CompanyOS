from __future__ import annotations

from dataclasses import dataclass

from companyos.runtime.opportunity_discovery import OpportunityDiscoveryStore
from companyos.runtime.research_evidence_pipeline import ResearchEvidenceEvaluator


@dataclass(frozen=True)
class OpportunityResearchDecision:
    opportunity_id: str
    decision: str
    reason: str
    score_before: float
    score_after: float


class OpportunityResearchBridge:
    """
    Applies research assessment back onto Phase 106 opportunity records.
    """

    def __init__(
        self,
        store: OpportunityDiscoveryStore | None = None,
        evaluator: ResearchEvidenceEvaluator | None = None,
    ) -> None:
        self.store = store or OpportunityDiscoveryStore()
        self.evaluator = evaluator or ResearchEvidenceEvaluator()

    def apply(self, opportunity_id: str) -> OpportunityResearchDecision:
        opportunity = self.store.load(opportunity_id)
        assessment = self.evaluator.assess(opportunity_id)

        before = opportunity.score

        if assessment.decision == "advance":
            adjustment = 10.0
        elif assessment.decision == "reject_or_revise":
            adjustment = -25.0
        elif assessment.decision == "hold":
            adjustment = -5.0
        else:
            adjustment = -2.0

        opportunity.score = max(0.0, min(100.0, opportunity.score + adjustment))
        opportunity.metadata["research_assessment"] = {
            "decision": assessment.decision,
            "reason": assessment.reason,
            "support_score": assessment.support_score,
            "contradiction_score": assessment.contradiction_score,
            "evidence_quality_score": assessment.evidence_quality_score,
            "confidence_score": assessment.confidence_score,
            "evidence_count": assessment.evidence_count,
        }
        self.store.save(opportunity)

        return OpportunityResearchDecision(
            opportunity_id=opportunity_id,
            decision=assessment.decision,
            reason=assessment.reason,
            score_before=before,
            score_after=opportunity.score,
        )
