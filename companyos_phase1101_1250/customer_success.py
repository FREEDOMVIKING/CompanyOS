class CustomerSuccessEngine:
    """1161-1170: churn risk, retention, and expansion signals."""
    def evaluate(self, customers):
        rows=[]
        for c in customers or []:
            usage=float(c.get("usage_score",0))
            support=max(0,float(c.get("support_burden",0)))
            payment=float(c.get("payment_health",1))
            satisfaction=float(c.get("satisfaction",0.5))
            health=max(0,min(1,usage*0.35+(1-min(1,support))*0.15+payment*0.2+satisfaction*0.3))
            rows.append({
                "id":c.get("id"),
                "health_score":round(health,3),
                "churn_risk":health<0.45,
                "expansion_signal":health>0.8 and usage>0.75
            })
        return rows
