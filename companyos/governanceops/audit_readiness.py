class AuditReadinessEngine:
    def score(self, signals):
        keys=["policy_registry","control_mapping","evidence","decision_ledger","access_review"]
        score=sum(1 for k in keys if signals.get(k))/len(keys)
        return {"score":round(score,3),"audit_ready":score>=.8}
