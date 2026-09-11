class RiskRegister:
    def prioritize(self, risks):
        rows=[]
        for r in risks or []:
            likelihood=float(r.get("likelihood",0))
            impact=float(r.get("impact",0))
            detectability=float(r.get("detectability",.5))
            score=likelihood*impact*(1+(1-detectability)*.5)
            rows.append({**r,"risk_score":round(score,4)})
        return sorted(rows,key=lambda x:x["risk_score"],reverse=True)
