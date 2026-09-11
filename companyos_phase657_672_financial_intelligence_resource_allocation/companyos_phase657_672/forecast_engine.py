class ForecastEngine:
    """666: simple deterministic financial scenarios."""

    def scenarios(self, metrics):
        mrr=float(metrics.get("mrr",0))
        costs=float(metrics.get("variable_costs",0))+float(metrics.get("fixed_costs",0))
        return {
            "conservative":{"next_month_mrr":round(mrr*0.9,2),"next_month_costs":round(costs*1.05,2)},
            "base":{"next_month_mrr":round(mrr*1.05,2),"next_month_costs":round(costs,2)},
            "upside":{"next_month_mrr":round(mrr*1.2,2),"next_month_costs":round(costs*1.05,2)},
        }
