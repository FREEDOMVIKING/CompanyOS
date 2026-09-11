class PriorityEngine:
    def score(self, item):
        impact=float(item.get("impact",0))
        urgency=float(item.get("urgency",0))
        confidence=float(item.get("confidence",0.5))
        risk=float(item.get("risk",0))
        effort=max(0.1,float(item.get("effort",1)))
        return round(((impact*0.35)+(urgency*0.25)+(confidence*0.2)+((1-risk)*0.2))/effort,4)

    def rank(self, items):
        rows=[{**x,"priority_score":self.score(x)} for x in (items or [])]
        return sorted(rows,key=lambda x:x["priority_score"],reverse=True)
