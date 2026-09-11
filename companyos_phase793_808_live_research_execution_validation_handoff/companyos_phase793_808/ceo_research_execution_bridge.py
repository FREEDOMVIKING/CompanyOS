from .closed_loop_integration import ClosedLoopIntegration
from .research_runtime_health import ResearchRuntimeHealth

class CEOResearchExecutionBridge:
    """807: CEO-facing live research integration interface."""

    def __init__(self, root):
        self.integration = ClosedLoopIntegration(root)

    def process(self, mission, execution_result=None):
        result = self.integration.process(mission, execution_result)
        if result.get("handled"):
            result["health"] = ResearchRuntimeHealth().evaluate(result.get("research_cycle"))
        return result
