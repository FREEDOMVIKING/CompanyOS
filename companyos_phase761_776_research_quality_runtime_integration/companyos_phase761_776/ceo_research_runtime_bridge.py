from .integrated_research_executor import IntegratedResearchExecutor
from .research_audit import ResearchAudit
class CEOResearchRuntimeBridge:
    """776: CEO-facing provider-aware research runtime bridge."""
    def __init__(self,root):
        self.executor=IntegratedResearchExecutor(root)
        self.audit=ResearchAudit(root)
    def evaluate(self,mission,raw_result,providers):
        result=self.executor.evaluate_result(mission,raw_result,providers)
        self.audit.append("research_evaluated",result)
        return result
