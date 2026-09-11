from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from companyos.runtime.autonomous_goal_intake import AutonomousGoalIntake
from companyos.runtime.goal_source_policy import GoalSourcePolicy


@dataclass(frozen=True)
class GuardedIntakeResult:
    accepted: bool
    intake_id: str | None
    reason: str
    requires_human_approval: bool
    external_action_requested: bool
    financial_action_requested: bool


class PolicyGuardedGoalIntake:
    """
    Applies Phase 105 policy before creating a Phase 103 durable intake record.
    """

    def __init__(
        self,
        intake: AutonomousGoalIntake | None = None,
        policy: GoalSourcePolicy | None = None,
    ) -> None:
        self.intake = intake or AutonomousGoalIntake()
        self.policy = policy or GoalSourcePolicy()

    def submit(
        self,
        *,
        goal: str,
        priority: int = 100,
        source: str = "manual",
        metadata: dict[str, Any] | None = None,
        intake_id: str | None = None,
    ) -> GuardedIntakeResult:
        decision = self.policy.evaluate(
            goal=goal,
            source=source,
            priority=priority,
            metadata=metadata,
        )

        if not decision.accepted:
            return GuardedIntakeResult(
                False, None, decision.reason,
                decision.requires_human_approval,
                decision.external_action_requested,
                decision.financial_action_requested,
            )

        merged = dict(metadata or {})
        merged.update({
            "source": decision.source,
            "requires_human_approval": decision.requires_human_approval,
            "external_action_requested": decision.external_action_requested,
            "financial_action_requested": decision.financial_action_requested,
            "phase105_policy_reason": decision.reason,
        })

        record = self.intake.submit(
            goal=decision.normalized_goal,
            priority=decision.priority,
            metadata=merged,
            intake_id=intake_id,
        )

        return GuardedIntakeResult(
            True,
            record.intake_id,
            decision.reason,
            decision.requires_human_approval,
            decision.external_action_requested,
            decision.financial_action_requested,
        )
