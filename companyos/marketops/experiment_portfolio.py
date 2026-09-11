class ExperimentPortfolio:
    def prioritize(self, experiments):
        rows=[]
        for e in experiments or []:
            impact=float(e.get("impact",0))
            confidence=float(e.get("confidence",0.5))
            effort=max(.1,float(e.get("effort",1)))
            risk=float(e.get("risk",0))
            score=(impact*confidence*(1-risk))/effort
            rows.append({**e,"experiment_score":round(score,4)})
        return sorted(rows,key=lambda x:x["experiment_score"],reverse=True)
