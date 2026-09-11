class BudgetEnvelope:
    """661: bounded recommendation envelope, not automatic spending authority."""

    def recommend(self, metrics):
        revenue=float(metrics.get("revenue",0))
        cash=float(metrics.get("cash_available",0))
        cap=min(max(0.0,revenue*0.2), max(0.0,cash*0.05))
        return {
            "recommended_experiment_cap":round(cap,2),
            "automatic_spend_authorized":False,
            "requires_explicit_financial_approval":True,
        }
