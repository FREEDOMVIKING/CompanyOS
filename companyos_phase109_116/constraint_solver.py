class ConstraintSolver:
    """111: choose highest-value feasible work under budget/capacity constraints."""
    def solve(self,items,budget,capacity):
        budget=float(budget);capacity=float(capacity);chosen=[];used_b=used_c=0.0
        ranked=sorted(items,key=lambda x:float(x.get("value",0))/max(.0001,float(x.get("cost",1))+float(x.get("capacity",1))),reverse=True)
        for x in ranked:
            c=max(0,float(x.get("cost",0)));cap=max(0,float(x.get("capacity",0)))
            if used_b+c<=budget and used_c+cap<=capacity:
                chosen.append(x);used_b+=c;used_c+=cap
        return {"chosen":chosen,"budget_used":round(used_b,2),"capacity_used":round(used_c,2)}
