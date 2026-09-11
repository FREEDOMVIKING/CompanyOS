class OrphanRecovery:
    def recover(self, jobs, tick):
        recovered=[]
        for j in jobs or []:
            if j.get("status")=="running" and int(tick) > int(j.get("lease_expiry_tick",0)):
                x=dict(j)
                x["status"]="retry"
                x["claimed_by"]=None
                recovered.append(x)
        return recovered
