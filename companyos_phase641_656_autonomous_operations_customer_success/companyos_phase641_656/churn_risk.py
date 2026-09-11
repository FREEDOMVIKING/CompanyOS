class ChurnRisk:
    """644: detect churn risk from customer health and behavioral signals."""

    def evaluate(self, customer, health):
        reasons=[]
        if health.get("health_score",1) < 0.4: reasons.append("low_customer_health")
        if float(customer.get("usage_change_30d",0)) <= -0.4: reasons.append("usage_decline")
        if int(customer.get("unresolved_tickets",0)) >= 3: reasons.append("support_friction")
        if customer.get("cancellation_intent"): reasons.append("cancellation_intent")
        if customer.get("payment_risk"): reasons.append("payment_risk")
        return {
            "at_risk":bool(reasons),
            "risk_level":"high" if len(reasons)>=3 else "medium" if reasons else "low",
            "reasons":reasons,
        }
