class OpportunityRanker:
    def rank(self, opportunities):
        rows=[]
        for o in opportunities or []:
            value=float(o.get("value",0)); confidence=float(o.get("confidence",0))
            speed=float(o.get("speed",0)); effort=max(.05,float(o.get("effort",1)))
            risk=float(o.get("risk",0))
            score=(value*confidence*speed*(1-risk))/effort
            rows.append({**o,"priority_score":round(score,4)})
        return sorted(rows,key=lambda x:x["priority_score"],reverse=True)
