from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class BudgetDecision:
    allowed: bool
    requested: float
    limit: float
    reason: str
    requires_approval: bool

class BudgetGuard:
    def evaluate(self,requested,limit):
        requested=float(requested); limit=float(limit)
        allowed=requested<=limit
        return BudgetDecision(
            allowed=allowed,
            requested=requested,
            limit=limit,
            reason="within_budget" if allowed else "budget_exceeded",
            requires_approval=not allowed,
        )
