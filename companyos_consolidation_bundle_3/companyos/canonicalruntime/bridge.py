from __future__ import annotations
from typing import Any, Dict
from companyos.canonicalorchestration import CanonicalOrchestrationBridge, GoalRequest
from .observer import RuntimeCycleObserver
from .opportunity_bridge import OpportunityResearchBridge

class UnifiedCEOCanonicalBridge:
    """
    Non-destructive bridge for Phase 101/102 and later CEO runtimes.

    Existing runtimes may explicitly call submit_ceo_goal(), submit_opportunity(),
    or submit_research_result(). This bundle does not monkey-patch or replace them.
    """

    def __init__(self, companyos_root: str | None = None):
        self.orchestration = CanonicalOrchestrationBridge(companyos_root)
        self.opportunities = OpportunityResearchBridge(companyos_root)
        self.observer = RuntimeCycleObserver(companyos_root)

    def status(self) -> Dict[str, Any]:
        out = {
            "ready": True,
            "reason": "unified_ceo_canonical_bridge_ready",
            "orchestration": self.orchestration.status(),
            "phase102_observation": self.observer.phase102_status(),
        }
        self.observer.record("bridge_status", out)
        return out

    def submit_ceo_goal(
        self,
        objective: str,
        context: Dict[str, Any] | None = None,
        *,
        source: str = "phase101_102_ceo",
        goal_id: str = "",
    ) -> Dict[str, Any]:
        goal = GoalRequest(
            objective=objective,
            context=context or {},
            source=source,
            goal_id=goal_id,
        )
        self.observer.record("ceo_goal_received", goal.to_dict())
        result = self.orchestration.run_goal(goal).to_dict()
        self.observer.record("ceo_goal_completed", result)
        return result

    def submit_opportunity(self, title: str, **kwargs) -> Dict[str, Any]:
        self.observer.record("opportunity_received", {"title": title, **kwargs})
        result = self.opportunities.opportunity_to_goal(title, **kwargs)
        self.observer.record("opportunity_goal_completed", result)
        return result

    def submit_research_result(self, research_question: str, **kwargs) -> Dict[str, Any]:
        self.observer.record("research_received", {"research_question": research_question, **kwargs})
        result = self.opportunities.research_to_goal(research_question, **kwargs)
        self.observer.record("research_goal_completed", result)
        return result
