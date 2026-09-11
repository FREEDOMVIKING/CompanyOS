from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GoalPolicyDecision:
    accepted: bool
    reason: str
    normalized_goal: str
    priority: int
    source: str
    requires_human_approval: bool
    external_action_requested: bool
    financial_action_requested: bool


class GoalSourcePolicy:
    """
    Phase 105 policy gate for CEO goal intake.

    Purpose:
    - normalize incoming goals
    - classify source
    - detect requests that imply external/financial action
    - keep those goals internal-only unless later explicitly approved
    - reject empty/oversized/untrusted payloads

    This layer does not execute external actions.
    """

    MAX_GOAL_CHARS = 4000

    EXTERNAL_MARKERS = (
        "send email",
        "send message",
        "publish",
        "post to",
        "deploy",
        "buy ",
        "purchase",
        "pay ",
        "transfer",
        "withdraw",
        "broadcast transaction",
        "sign transaction",
        "move funds",
    )

    FINANCIAL_MARKERS = (
        "buy ",
        "purchase",
        "pay ",
        "transfer",
        "withdraw",
        "move funds",
        "sign transaction",
        "broadcast transaction",
        "trade ",
        "swap ",
    )

    def evaluate(
        self,
        *,
        goal: str,
        source: str = "manual",
        priority: int = 100,
        metadata: dict[str, Any] | None = None,
    ) -> GoalPolicyDecision:
        normalized = " ".join(str(goal).strip().split())
        source = (source or "manual").strip().lower()
        metadata = dict(metadata or {})

        if not normalized:
            return GoalPolicyDecision(
                False, "goal_empty", "", int(priority), source,
                False, False, False
            )

        if len(normalized) > self.MAX_GOAL_CHARS:
            return GoalPolicyDecision(
                False, "goal_too_large", normalized[:self.MAX_GOAL_CHARS],
                int(priority), source, False, False, False
            )

        lowered = normalized.lower()
        external = any(marker in lowered for marker in self.EXTERNAL_MARKERS)
        financial = any(marker in lowered for marker in self.FINANCIAL_MARKERS)

        # Phase 105 allows intake but marks sensitive goals for approval.
        requires_approval = external or financial

        bounded_priority = max(1, min(1000, int(priority)))

        return GoalPolicyDecision(
            accepted=True,
            reason="accepted_with_approval_required" if requires_approval else "accepted_internal_goal",
            normalized_goal=normalized,
            priority=bounded_priority,
            source=source,
            requires_human_approval=requires_approval,
            external_action_requested=external,
            financial_action_requested=financial,
        )
