from .growth_intelligence_manager import GrowthIntelligenceManager
from .growth_audit import GrowthAudit

class CEOGrowthBridge:
    """639: CEO-facing growth planning/evaluation bridge."""

    def __init__(self, root=None):
        self.root=root

    def plan(self, venture, channels):
        return GrowthIntelligenceManager().plan(venture,channels)

    def evaluate(self, venture_id, metrics):
        result=GrowthIntelligenceManager().evaluate(metrics)
        if self.root:
            GrowthAudit(self.root).append(venture_id,result)
        return result
