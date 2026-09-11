class ActionRiskScorer:
    def score(self, action):
        risk=0.0
        if action.get("external",True): risk+=0.2
        if not action.get("reversible",False): risk+=0.25
        amount=float(action.get("amount",0) or 0)
        if amount>=500: risk+=0.2
        if amount>=5000: risk+=0.15
        if action.get("kind") in {"legal_filing","contract_signature","bank_transfer","production_deploy"}:
            risk+=0.2
        return {"risk_score":round(min(1,risk),3),
                "risk_level":"high" if risk>=.7 else ("medium" if risk>=.4 else "low")}
