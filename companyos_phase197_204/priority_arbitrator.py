class PriorityArbitrator:
    """202: continuously arbitrate competing autonomous initiatives."""
    def rank(self,items):
        rows=[]
        for x in items:
            score=float(x.get("impact",0))*.35+float(x.get("urgency",0))*.2+float(x.get("evidence",0))*.25+float(x.get("learning",0))*.15-float(x.get("risk",0))*.1
            rows.append({**x,"priority_score":round(score,4)})
        return sorted(rows,key=lambda x:x["priority_score"],reverse=True)
