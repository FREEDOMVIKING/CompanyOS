from __future__ import annotations

from typing import Any, Dict
from .bridge import CanonicalOrchestrationBridge
from .contracts import GoalRequest

class CEORuntimeCanonicalAdapter:
    """
    Adapter intended for Phase 101/102 or later CEO runtimes.

    It does not monkey-patch existing runtimes.
    A caller explicitly submits a goal through this adapter.
    """

    def __init__(self, companyos_root: str | None = None):
        self.bridge = CanonicalOrchestrationBridge(companyos_root)

    def submit_goal(
        self,
        objective: str,
        context: Dict[str, Any] | None = None,
        *,
        source: str = "ceo_runtime",
        goal_id: str = "",
    ) -> Dict[str, Any]:
        goal = GoalRequest(
            objective=objective,
            context=context or {},
            source=source,
            goal_id=goal_id,
        )
        return self.bridge.run_goal(goal).to_dict()
