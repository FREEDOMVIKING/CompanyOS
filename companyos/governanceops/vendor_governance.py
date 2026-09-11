class VendorGovernanceEngine:
    def evaluate(self, vendors):
        rows=[]
        for v in vendors or []:
            risk=float(v.get("risk",0))
            critical=bool(v.get("critical",False))
            rows.append({
                **v,
                "review_required":critical or risk>=.5,
                "fallback_required":critical,
                "status":"review" if critical or risk>=.5 else "standard"
            })
        return rows
