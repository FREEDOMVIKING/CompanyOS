class CustomerAcquisitionEngine:
    """1111-1120: rank channels and generate acquisition plan."""
    def plan(self, channels, budget, target_cac=None):
        rows=[]
        for c in channels or []:
            cost=float(c.get("cost",0))
            leads=float(c.get("leads",0))
            conv=float(c.get("conversion_rate",0))
            customers=leads*conv
            cac=(cost/customers) if customers else None
            score=0.0
            if cac is not None:
                score=1/(1+cac)
            rows.append({**c,"estimated_customers":round(customers,2),"cac":None if cac is None else round(cac,2),"score":score})
        rows=sorted(rows,key=lambda x:x["score"],reverse=True)
        selected=[]
        remaining=float(budget)
        for r in rows:
            if remaining<=0: break
            cap=min(float(r.get("recommended_spend", r.get("cost",0))), remaining)
            if target_cac is None or r.get("cac") is None or r.get("cac")<=float(target_cac):
                selected.append({"channel":r.get("name"),"allocated_budget":round(cap,2),"cac":r.get("cac")})
                remaining-=cap
        return {"selected_channels":selected,"unallocated_budget":round(remaining,2),"ranked_channels":rows}
