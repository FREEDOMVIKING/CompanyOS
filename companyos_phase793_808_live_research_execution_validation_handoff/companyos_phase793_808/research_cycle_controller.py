from .multi_provider_runtime_adapter import MultiProviderRuntimeAdapter
from .quality_handoff_gate import QualityHandoffGate
from .validation_handoff import ValidationHandoff
from .research_next_action import ResearchNextAction
from .deferred_mission_policy import DeferredMissionPolicy
from .provider_chain_state import ProviderChainState
from .research_execution_audit import ResearchExecutionAudit

class ResearchCycleController:
    """803: orchestrate research execution -> quality gate -> next action."""

    def __init__(self, root):
        self.root = root
        self.adapter = MultiProviderRuntimeAdapter(root)
        self.state = ProviderChainState(root)
        self.audit = ResearchExecutionAudit(root)

    def run(self, mission, execution_result=None):
        result = self.adapter.execute(mission, execution_result)
        gate = QualityHandoffGate().evaluate(result)
        action = ResearchNextAction().decide(gate, result)

        next_mission = None
        if action == "handoff_to_validation":
            next_mission = ValidationHandoff().build(mission, result)
        elif action in ("continue_research", "defer_and_research_later"):
            next_mission = DeferredMissionPolicy().build(
                mission,
                fallback_provider=result.get("fallback_provider"),
            )

        self.state.save(mission.get("mission_id"), result)
        self.audit.append("research_cycle", {
            "mission_id": mission.get("mission_id"),
            "action": action,
            "gate": gate,
            "result": result,
            "next_mission": next_mission,
        })

        return {
            "success": True,
            "status": "live_research_cycle_complete",
            "action": action,
            "gate": gate,
            "research_result": result,
            "next_mission": next_mission,
        }
