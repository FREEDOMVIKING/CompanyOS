class PortfolioKPIs:
    """681: roll up portfolio-level KPIs."""

    def calculate(self, ventures):
        total_mrr=sum(float(v.get("mrr",0)) for v in ventures)
        total_profit=sum(float(v.get("profit",0)) for v in ventures)
        active=sum(1 for v in ventures if v.get("status") not in ("killed","paused"))
        profitable=sum(1 for v in ventures if float(v.get("profit",0)) > 0)
        return {
            "venture_count":len(ventures),
            "active_ventures":active,
            "profitable_ventures":profitable,
            "total_mrr":round(total_mrr,2),
            "total_profit":round(total_profit,2),
        }
