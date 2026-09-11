class PortfolioAllocator:
    def allocate(self, ventures, capital, slots):
        rows=[]
        for v in ventures or []:
            score=(float(v.get("growth_score",0))*0.3+
                   float(v.get("validation_confidence",0))*0.25+
                   float(v.get("gross_margin",0))*0.2+
                   float(v.get("strategic_fit",0.5))*0.15+
                   float(v.get("health_score",1))*0.1)
            rows.append({**v,"portfolio_score":round(score,3)})
        rows=sorted(rows,key=lambda x:x["portfolio_score"],reverse=True)
        denom=sum(max(0,r["portfolio_score"]) for r in rows) or 1
        remaining_slots=int(slots)
        out=[]
        for r in rows:
            budget=float(capital)*(max(0,r["portfolio_score"])/denom)
            granted=1 if remaining_slots>0 else 0
            remaining_slots-=granted
            out.append({"venture_id":r.get("venture_id"),"budget":round(budget,2),
                        "agent_slots":granted,"score":r["portfolio_score"]})
        return out
