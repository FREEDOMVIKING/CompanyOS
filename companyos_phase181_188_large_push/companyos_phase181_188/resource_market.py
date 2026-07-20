class InternalResourceMarket:
    """186: dynamically allocate internal capacity to highest-value initiatives."""
    def allocate(self,initiatives,total):
        total=max(0,float(total)); scored=[]
        for i in initiatives:
            score=max(0,float(i.get("expected_value",0))*.45+float(i.get("evidence",0))*.3+float(i.get("learning",0))*.2-float(i.get("risk",0))*.15)
            scored.append((score,i))
        denom=sum(x[0] for x in scored)
        return [{"initiative":i.get("name"),"capacity":round(total*s/denom,4) if denom else 0,"autonomous":True} for s,i in scored]
