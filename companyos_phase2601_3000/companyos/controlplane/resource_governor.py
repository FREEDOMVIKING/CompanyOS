class ResourceGovernor:
    def allocate(self, claims, total_units):
        claims=sorted(claims or [],key=lambda x:float(x.get("priority",0)),reverse=True)
        left=int(total_units); out=[]
        for c in claims:
            need=max(1,int(c.get("units",1)))
            grant=min(need,left)
            out.append({"owner":c.get("owner"),"resource":c.get("resource"),"granted":grant})
            left-=grant
            if left<=0:break
        return {"allocations":out,"remaining":max(0,left)}
