from companyos_phase673_688 import PortfolioPriority, PortfolioActionPolicy, PortfolioKPIs

class PortfolioBridge:
    """713: portfolio-level review adapter."""

    def review(self, ventures):
        enriched = []
        for v in ventures or []:
            item = dict(v)
            item["portfolio_score"] = PortfolioPriority().score(item)
            item["portfolio_action"] = PortfolioActionPolicy().decide(item)
            enriched.append(item)
        enriched.sort(key=lambda x: x["portfolio_score"], reverse=True)
        return {
            "ventures": enriched,
            "kpis": PortfolioKPIs().calculate(enriched),
        }
