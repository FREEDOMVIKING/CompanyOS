class BudgetArbitrator:
    def allocate(self, requests, total_budget):
        req=list(requests or [])
        scored=[]
        for r in req:
            value=float(r.get("expected_value",0))
            confidence=float(r.get("confidence",0.5))
            urgency=float(r.get("urgency",0.5))
            score=value*0.5+confidence*0.3+urgency*0.2
            scored.append({**r,"allocation_score":score})
        scored=sorted(scored,key=lambda x:x["allocation_score"],reverse=True)

        remaining=float(total_budget)
        out=[]
        for r in scored:
            ask=float(r.get("requested",0))
            cap=float(r.get("autonomous_cap",500))
            grant=min(ask,cap,remaining)
            out.append({"department":r.get("department"),"requested":ask,"granted":round(grant,2),
                        "requires_approval":ask>cap})
            remaining-=grant
            if remaining<=0: break
        return {"allocations":out,"reserve":round(max(0,remaining),2)}
