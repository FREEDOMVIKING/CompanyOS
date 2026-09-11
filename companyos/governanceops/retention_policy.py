class RetentionPolicyEngine:
    def evaluate(self, records):
        out=[]
        for r in records or []:
            category=r.get("category","operational")
            days={"audit":2555,"financial":2555,"customer":1095,"operational":365}.get(category,365)
            out.append({**r,"retention_days":days,"deletion_requires_policy_check":True})
        return out
