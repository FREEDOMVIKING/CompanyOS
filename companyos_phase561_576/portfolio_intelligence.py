from .venture_scorecard import VentureScorecard
from .portfolio_compare import PortfolioCompare
from .capital_attention import CapitalAttention

class PortfolioIntelligence:
    """574: compare ventures and allocate bounded CEO attention."""

    def analyze(self, ventures):
        scored=[]
        for v in ventures:
            evidence=v.get("evidence") or {}
            s=VentureScorecard().score(evidence)
            scored.append({**v,"score":s["score"],"scorecard":s})
        ranked=PortfolioCompare().rank(scored)
        return {
            "success":True,
            "status":"portfolio_intelligence_ready",
            "ranked":ranked,
            "attention":CapitalAttention().allocate(ranked,2),
        }
