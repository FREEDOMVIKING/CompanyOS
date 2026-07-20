class RiskRegister:
    """88: structured enterprise risk register."""
    def assess(self,risks):
        out=[]
        for r in risks:
            likelihood=max(0,min(5,float(r.get("likelihood",0))))
            impact=max(0,min(5,float(r.get("impact",0))))
            score=likelihood*impact
            out.append({**r,"risk_score":round(score,2),
                        "level":"critical" if score>=16 else "high" if score>=10 else "medium" if score>=5 else "low"})
        return sorted(out,key=lambda x:x["risk_score"],reverse=True)
