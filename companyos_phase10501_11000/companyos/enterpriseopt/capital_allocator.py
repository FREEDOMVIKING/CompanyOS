class EnterpriseCapitalAllocator:
    def allocate(self, ventures, capital):
        rows=list(ventures or [])
        total=sum(max(.01,float(v.get("enterprise_score",0))) for v in rows) or 1
        out=[]
        for v in rows:
            weight=max(.01,float(v.get("enterprise_score",0)))/total
            out.append({
                "venture_id":v.get("venture_id"),
                "allocation":round(float(capital)*weight,2),
                "weight":round(weight,4)
            })
        return out
