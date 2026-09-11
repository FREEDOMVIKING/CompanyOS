class CustomerHealthEngine:
    def score(self, customers):
        out=[]
        for c in customers or []:
            usage=float(c.get("usage",0)); satisfaction=float(c.get("satisfaction",0))
            payment=float(c.get("payment_health",1)); support=max(0,1-float(c.get("support_friction",0)))
            score=usage*.3+satisfaction*.3+payment*.2+support*.2
            out.append({**c,"health_score":round(score,4),"health":"healthy" if score>=.75 else ("watch" if score>=.5 else "at_risk")})
        return sorted(out,key=lambda x:x["health_score"])
