class InnovationPortfolioEngine:
    def allocate(self, bets, budget):
        rows=[]
        for b in bets or []:
            upside=float(b.get("upside",0))
            confidence=float(b.get("confidence",0))
            strategic=float(b.get("strategic_value",0))
            risk=float(b.get("risk",0))
            score=upside*.35+confidence*.25+strategic*.25+(1-risk)*.15
            rows.append({**b,"innovation_score":round(score,4)})
        rows=sorted(rows,key=lambda x:x["innovation_score"],reverse=True)
        total=sum(max(.01,x["innovation_score"]) for x in rows) or 1
        return [{**x,"recommended_budget":round(float(budget)*max(.01,x["innovation_score"])/total,2)} for x in rows]
