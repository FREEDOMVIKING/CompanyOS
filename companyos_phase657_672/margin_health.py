class MarginHealth:
    """660: gross-margin and churn health."""

    def evaluate(self, snapshot):
        margin=float(snapshot.get("gross_margin_rate",0))
        churn=float(snapshot.get("monthly_churn_rate",0))
        if margin >= 0.75 and churn <= 0.05:
            level="strong"
        elif margin >= 0.5 and churn <= 0.1:
            level="acceptable"
        else:
            level="weak"
        return {"level":level,"gross_margin_rate":margin,"monthly_churn_rate":churn}
