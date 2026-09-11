from .financial_manager import FinancialManager
from .roi_score import ROIScore
from .resource_efficiency import ResourceEfficiency
from .portfolio_capital_rank import PortfolioCapitalRank
from .financial_audit import FinancialAudit

class CEOFinancialBridge:
    """670: CEO-facing financial intelligence and portfolio ranking."""

    def __init__(self, root=None):
        self.root=root

    def review_venture(self, venture_id, metrics, previous=None):
        result=FinancialManager().review(metrics,previous)
        if self.root:
            FinancialAudit(self.root).append(venture_id,result)
        return result

    def rank_portfolio(self, ventures):
        enriched=[]
        for v in ventures:
            item=dict(v)
            item["roi_score"]=ROIScore().score(item)
            item["resource_efficiency"]=ResourceEfficiency().score(item)
            enriched.append(item)
        return PortfolioCapitalRank().rank(enriched)
