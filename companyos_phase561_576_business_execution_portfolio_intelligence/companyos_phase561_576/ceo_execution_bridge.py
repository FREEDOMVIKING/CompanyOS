from .business_execution_manager import BusinessExecutionManager
from .portfolio_intelligence import PortfolioIntelligence

class CEOExecutionBridge:
    """575: CEO-facing business execution and portfolio bridge."""

    def venture_review(self, venture, evidence):
        return BusinessExecutionManager().review(venture,evidence)

    def portfolio_review(self, ventures):
        return PortfolioIntelligence().analyze(ventures)
