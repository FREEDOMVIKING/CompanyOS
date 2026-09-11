class CrossVentureResourceScheduler:
    def allocate(self, ventures, available_slots):
        ventures=sorted(ventures or [], key=lambda v:float(v.get("priority_score",0)), reverse=True)
        slots=int(available_slots)
        out=[]
        for v in ventures:
            need=max(1,int(v.get("requested_slots",1)))
            grant=min(need,slots)
            out.append({"venture_id":v.get("venture_id"),"granted_slots":grant})
            slots-=grant
            if slots<=0: break
        return {"allocations":out,"remaining_slots":max(0,slots)}
