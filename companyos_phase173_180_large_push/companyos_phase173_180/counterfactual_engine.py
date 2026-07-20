class CounterfactualEngine:
    """175: compare candidate strategies before committing internal capacity."""
    def rank(self, scenarios):
        rows=[]
        for s in scenarios:
            upside=float(s.get("upside",0));prob=float(s.get("probability",0));learning=float(s.get("learning",0));risk=float(s.get("risk",0))
            score=upside*prob*.55+learning*.25-risk*.20
            rows.append({**s,"counterfactual_score":round(score,4)})
        return sorted(rows,key=lambda x:x["counterfactual_score"],reverse=True)
