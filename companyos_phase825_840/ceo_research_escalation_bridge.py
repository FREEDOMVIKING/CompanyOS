from .research_escalation_controller import ResearchEscalationController

class CEOResearchEscalationBridge:
    """839: CEO-facing escalation interface."""

    def __init__(self, root):
        self.controller = ResearchEscalationController(root)

    def run(self, mission, provider_results=None, max_total_attempts=8):
        return self.controller.run(
            mission,
            provider_results=provider_results or {},
            max_total_attempts=max_total_attempts,
        )
