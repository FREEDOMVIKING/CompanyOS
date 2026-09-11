class CustomerHealth:
    """641: score customer health from usage, value, support, and payment signals."""

    def score(self, customer):
        usage = max(0.0, min(1.0, float(customer.get("usage_score",0))))
        value = max(0.0, min(1.0, float(customer.get("value_realization",0))))
        satisfaction = max(0.0, min(1.0, float(customer.get("satisfaction_score",0))))
        support_penalty = min(1.0, int(customer.get("open_critical_issues",0))*0.35)
        payment_penalty = 0.4 if customer.get("payment_risk") else 0.0
        score = (usage*0.3)+(value*0.35)+(satisfaction*0.35)-support_penalty-payment_penalty
        score = round(max(0.0,min(1.0,score)),3)
        return {
            "health_score":score,
            "status":"healthy" if score>=0.7 else "watch" if score>=0.4 else "at_risk",
        }
