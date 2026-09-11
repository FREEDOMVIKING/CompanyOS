from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from companyos.runtime.opportunity_discovery import OpportunityDiscoveryStore, OpportunityRecord
from companyos.runtime.policy_guarded_goal_intake import PolicyGuardedGoalIntake


@dataclass(frozen=True)
class OpportunityGoalResult:
    generated: bool
    opportunity_id: Optional[str]
    intake_id: Optional[str]
    reason: str
    score: float
    requires_human_approval: bool


class OpportunityGoalGenerator:
    """
    Converts sufficiently strong opportunities into durable CEO goals.

    Rules:
    - minimum score threshold
    - no duplicate goal generation for same opportunity
    - Phase 105 policy gate remains authoritative
    """

    def __init__(
        self,
        *,
        store: OpportunityDiscoveryStore | None = None,
        guarded_intake: PolicyGuardedGoalIntake | None = None,
        min_score: float = 60.0,
    ) -> None:
        self.store = store or OpportunityDiscoveryStore()
        self.guarded_intake = guarded_intake or PolicyGuardedGoalIntake()
        self.min_score = float(min_score)

    def generate_from(self, opportunity: OpportunityRecord) -> OpportunityGoalResult:
        if opportunity.score < self.min_score:
            return OpportunityGoalResult(
                False,
                opportunity.opportunity_id,
                None,
                "below_score_threshold",
                opportunity.score,
                False,
            )

        metadata = dict(opportunity.metadata or {})
        if metadata.get("generated_intake_id"):
            return OpportunityGoalResult(
                False,
                opportunity.opportunity_id,
                metadata.get("generated_intake_id"),
                "already_generated",
                opportunity.score,
                bool(metadata.get("requires_human_approval", False)),
            )

        goal = (
            f"Investigate and develop the opportunity: {opportunity.title}. "
            f"{opportunity.description}"
        )

        result = self.guarded_intake.submit(
            goal=goal,
            priority=max(1, int(1000 - min(999, opportunity.score * 10))),
            source="opportunity_discovery",
            metadata={
                "opportunity_id": opportunity.opportunity_id,
                "opportunity_score": opportunity.score,
                "opportunity_source": opportunity.source,
                "opportunity_category": opportunity.category,
                "requires_external_action_hint": opportunity.requires_external_action,
                "requires_financial_action_hint": opportunity.requires_financial_action,
            },
            intake_id=f"opportunity-{opportunity.opportunity_id}",
        )

        opportunity.metadata["generated_intake_id"] = result.intake_id
        opportunity.metadata["requires_human_approval"] = result.requires_human_approval
        self.store.save(opportunity)

        return OpportunityGoalResult(
            generated=result.accepted,
            opportunity_id=opportunity.opportunity_id,
            intake_id=result.intake_id,
            reason=result.reason,
            score=opportunity.score,
            requires_human_approval=result.requires_human_approval,
        )

    def generate_best_available(self) -> OpportunityGoalResult:
        candidates = sorted(
            self.store.all_records(),
            key=lambda x: (-x.score, x.created_at_unix),
        )

        for opportunity in candidates:
            if opportunity.metadata.get("generated_intake_id"):
                continue
            return self.generate_from(opportunity)

        return OpportunityGoalResult(
            False, None, None, "no_eligible_opportunity", 0.0, False
        )
