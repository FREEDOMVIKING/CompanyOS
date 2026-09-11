from .runtime_research_guard import RuntimeResearchGuard
from .research_cycle_controller import ResearchCycleController
from .validation_queue_bridge import ValidationQueueBridge

class ClosedLoopIntegration:
    """806: safe adapter used by the unified closed-loop runtime."""

    def __init__(self, root):
        self.root = root
        self.controller = ResearchCycleController(root)

    def process(self, mission, execution_result=None):
        if not RuntimeResearchGuard().should_run(mission):
            return {
                "handled": False,
                "research_cycle": None,
                "next_mission": None,
            }

        cycle = self.controller.run(mission, execution_result)
        next_mission = ValidationQueueBridge().build(cycle.get("next_mission"))

        return {
            "handled": True,
            "research_cycle": cycle,
            "next_mission": next_mission or cycle.get("next_mission"),
        }
