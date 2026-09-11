class ProfitabilityEngine:
    def evaluate(self, ventures):
        out=[]
        for v in ventures or []:
            revenue=float(v.get("revenue",0))
            costs=float(v.get("costs",0))
            profit=revenue-costs
            margin=profit/revenue if revenue else 0
            out.append({
                "venture_id":v.get("venture_id"),
                "profit":round(profit,2),
                "margin":round(margin,3),
                "profitable":profit>0
            })
        return out
