class OpportunityEngine:
    def rank(self, candidates):
        out=[]
        for c in candidates or []:
            demand=float(c.get("demand",0))
            pain=float(c.get("pain",0))
            willingness=float(c.get("willingness_to_pay",0))
            competition=float(c.get("competition",0))
            evidence=float(c.get("evidence",0))
            score=.28*demand+.22*pain+.22*willingness+.18*evidence+.10*(1-competition)
            out.append({**c,"opportunity_score":round(score,4)})
        return sorted(out,key=lambda x:x["opportunity_score"],reverse=True)
