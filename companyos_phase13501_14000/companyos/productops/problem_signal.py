class ProblemSignalEngine:
    def rank(self, signals):
        rows=[]
        for s in signals or []:
            pain=float(s.get("pain",0))
            frequency=float(s.get("frequency",0))
            urgency=float(s.get("urgency",0))
            willingness=float(s.get("willingness_to_pay",0))
            score=pain*.35+frequency*.25+urgency*.2+willingness*.2
            rows.append({**s,"problem_score":round(score,4)})
        return sorted(rows,key=lambda x:x["problem_score"],reverse=True)
