class InitiativeManager:
    def prioritize(self, initiatives):
        rows=[]
        for i in initiatives or []:
            value=float(i.get("expected_value",0))
            confidence=float(i.get("confidence",0.5))
            effort=max(0.1,float(i.get("effort",1)))
            score=(value*confidence)/effort
            rows.append({**i,"priority_score":round(score,3)})
        return sorted(rows,key=lambda x:x["priority_score"],reverse=True)
