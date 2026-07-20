class AutonomousProductManager:
    """151: prioritize autonomous product backlog."""
    def prioritize(self, items, capacity=5):
        rows=[]
        for x in items:
            if x.get("blocked"): continue
            score=float(x.get("customer_value",0))*.4+float(x.get("business_value",0))*.3+float(x.get("learning",0))*.2-float(x.get("effort",0))*.1
            rows.append({**x,"product_score":round(score,4)})
        return sorted(rows,key=lambda x:x["product_score"],reverse=True)[:max(1,int(capacity))]
