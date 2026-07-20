class AdaptiveBudgeter:
    """161: allocate bounded internal experiment capacity based on evidence."""
    def allocate(self,items,total):
        total=max(0,float(total)); scores=[]
        for x in items:
            s=max(0,float(x.get("evidence",0))*.5+float(x.get("learning",0))*.3+(1-float(x.get("risk",0)))*.2)
            scores.append((s,x))
        denom=sum(s for s,_ in scores)
        return [{"name":x.get("name"),"allocation":round(total*s/denom,4) if denom else 0,
                 "autonomous_within_allocation":True} for s,x in scores]
