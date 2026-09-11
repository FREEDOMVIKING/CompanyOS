from __future__ import annotations
from typing import Any, Dict
from companyos.canonicalorchestration import CanonicalOrchestrationBridge, GoalRequest

class OpportunityResearchBridge:
    def __init__(self, companyos_root: str | None = None):
        self.orchestration = CanonicalOrchestrationBridge(companyos_root)

    def opportunity_to_goal(
        self,
        title: str,
        *,
        hypothesis: str = "",
        evidence: Dict[str, Any] | None = None,
        source: str = "opportunity_discovery",
        opportunity_id: str = "",
    ) -> Dict[str, Any]:
        context = {
            "opportunity_id": opportunity_id,
            "hypothesis": hypothesis,
            "evidence": evidence or {},
            "source": source,
        }
        objective = f"Evaluate and develop opportunity: {title}".strip()
        goal = GoalRequest(
            objective=objective,
            context=context,
            source=source,
        )
        return self.orchestration.run_goal(goal).to_dict()

    def research_to_goal(
        self,
        research_question: str,
        *,
        findings: Dict[str, Any] | None = None,
        source: str = "research_pipeline",
    ) -> Dict[str, Any]:
        goal = GoalRequest(
            objective=f"Turn research into an actionable company plan: {research_question}",
            context={"findings": findings or {}, "source": source},
            source=source,
        )
        return self.orchestration.run_goal(goal).to_dict()
