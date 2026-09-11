class ComplianceRegistry:
    def evaluate(self, obligations, evidence):
        evidence=set(evidence or [])
        rows=[]
        for o in obligations or []:
            key=o.get("key")
            met=key in evidence
            rows.append({**o,"met":met,"status":"satisfied" if met else "open"})
        return {
            "obligations":rows,
            "open_count":sum(1 for r in rows if not r["met"]),
            "ready":all(r["met"] for r in rows) if rows else True
        }
