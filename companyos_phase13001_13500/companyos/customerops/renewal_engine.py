class RenewalReadinessEngine:
    def evaluate(self, customers):
        return [{"customer_id":c.get("customer_id"),
                 "renewal_readiness":round(float(c.get("health_score",0))*.7+float(c.get("value_realization",.5))*.3,4)}
                for c in (customers or [])]
