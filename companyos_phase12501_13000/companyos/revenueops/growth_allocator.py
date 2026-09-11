class GrowthAllocator:
    def allocate(self, channels, budget):
        scored=[]
        for c in channels or []:
            score=float(c.get("roi",0))*float(c.get("confidence",.5))*(1-float(c.get("risk",0)))
            scored.append({**c,"allocation_score":max(0,score)})
        total=sum(x["allocation_score"] for x in scored) or 1
        return [{**x,"recommended_budget":round(float(budget)*x["allocation_score"]/total,2)} for x in scored]
