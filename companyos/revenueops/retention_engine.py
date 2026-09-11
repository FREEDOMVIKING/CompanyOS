class RetentionEngine:
    def analyze(self, customers):
        at_risk=[]; expansion=[]
        for c in customers or []:
            health=float(c.get("health",0))
            if health<.5: at_risk.append(c.get("customer_id"))
            if health>=.8 and float(c.get("usage_growth",0))>.1: expansion.append(c.get("customer_id"))
        return {"at_risk":at_risk,"expansion_candidates":expansion}
