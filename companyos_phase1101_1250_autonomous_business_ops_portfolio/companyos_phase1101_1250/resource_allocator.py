class ResourceAllocator:
    """1193-1204: allocate budget/agent capacity across ventures."""
    def allocate(self, ventures, total_budget, total_agent_slots):
        ranked=[]
        for v in ventures or []:
            score=(
                float(v.get("growth_score",0))*0.35+
                float(v.get("validation_confidence",0))*0.25+
                float(v.get("gross_margin",0))*0.2+
                float(v.get("strategic_fit",0.5))*0.2
            )
            ranked.append({**v,"allocation_score":round(score,3)})
        ranked=sorted(ranked,key=lambda x:x["allocation_score"],reverse=True)
        total_score=sum(max(0,r["allocation_score"]) for r in ranked) or 1
        out=[]
        slots=int(total_agent_slots)
        for i,r in enumerate(ranked):
            budget=float(total_budget)*(max(0,r["allocation_score"])/total_score)
            assigned=1 if slots>0 else 0
            slots-=assigned
            out.append({"venture_id":r.get("venture_id"),"budget":round(budget,2),"agent_slots":assigned,"score":r["allocation_score"]})
        return out
