class PriorityArbitrator:
    def rank(self, work_items):
        rows=[]
        for w in work_items or []:
            impact=float(w.get("impact",0))
            urgency=float(w.get("urgency",0))
            confidence=float(w.get("confidence",.5))
            effort=max(.1,float(w.get("effort",1)))
            risk=float(w.get("risk",0))
            score=(impact*.35+urgency*.25+confidence*.2+(1-risk)*.2)/effort
            rows.append({**w,"priority_score":round(score,4)})
        return sorted(rows,key=lambda x:x["priority_score"],reverse=True)
