class RevenueSignal:
    """635: normalize commercial traction strength."""

    def score(self, metrics):
        paying=int(metrics.get("paying_customers",0))
        revenue=float(metrics.get("revenue",0))
        retained=int(metrics.get("retained_customers",0))
        score=0
        if paying > 0: score += 2
        if revenue > 0: score += 2
        if retained > 0: score += 2
        if paying >= 5: score += 2
        if retained >= 3: score += 2
        return min(10,score)
