class CustomerSuccess:
    """120: identify churn risk and expansion candidates."""
    def analyze(self,customers):
        out=[]
        for c in customers:
            usage=float(c.get("usage",0));satisfaction=float(c.get("satisfaction",0));trend=float(c.get("trend",0))
            health=usage*.4+satisfaction*.4+max(0,min(1,(trend+1)/2))*.2
            out.append({**c,"health":round(health,4),"status":"healthy" if health>=.7 else "watch" if health>=.45 else "at_risk"})
        return out
