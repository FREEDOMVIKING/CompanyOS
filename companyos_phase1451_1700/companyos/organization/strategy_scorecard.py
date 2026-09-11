class StrategyScorecard:
    def evaluate(self, goals, outcomes):
        outcomes=outcomes or {}
        rows=[]
        for g in goals or []:
            achieved=float(outcomes.get(g.get("id"),0))
            rows.append({"goal_id":g.get("id"),"achievement":achieved,
                         "status":"on_track" if achieved>=0.7 else "at_risk"})
        overall=sum(x["achievement"] for x in rows)/max(1,len(rows))
        return {"overall":round(overall,3),"goals":rows}
