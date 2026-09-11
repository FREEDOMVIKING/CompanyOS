class GovernanceEngine:
    def review(self, decisions):
        out=[]
        for d in decisions or []:
            reversible=bool(d.get("reversible",False))
            external=bool(d.get("external",False))
            financial=float(d.get("financial_exposure",0))
            requires=(not reversible and external) or financial>=500
            out.append({**d,"requires_approval":requires})
        return out
