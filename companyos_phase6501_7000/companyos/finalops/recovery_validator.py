class RecoveryValidator:
    def validate(self, scenarios):
        out=[]
        for s in scenarios or []:
            expected=s.get("expected")
            actual=s.get("actual")
            out.append({**s,"passed":expected==actual})
        return {"passed":all(x["passed"] for x in out) if out else True,"scenarios":out}
