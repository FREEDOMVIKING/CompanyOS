class ExpansionSequencer:
    def sequence(self, opportunities):
        rows=[]
        for o in opportunities or []:
            reward=float(o.get("expansion_score",0))
            risk=float(o.get("risk_score",0))
            score=reward*(1-risk)
            rows.append({**o,"sequence_score":round(score,4)})
        return sorted(rows,key=lambda x:x["sequence_score"],reverse=True)
