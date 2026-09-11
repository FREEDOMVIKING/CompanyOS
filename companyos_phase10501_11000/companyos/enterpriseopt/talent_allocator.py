class TalentAllocator:
    def assign(self, agents, work):
        available=[dict(a) for a in agents or []]
        assignments=[]
        for w in sorted(work or [],key=lambda x:float(x.get("priority",0)),reverse=True):
            candidates=[]
            for a in available:
                match=float(a.get("skills",{}).get(w.get("skill"),0))
                load=float(a.get("load",0))
                score=match*(1-load)
                candidates.append((score,a))
            candidates.sort(key=lambda x:x[0],reverse=True)
            chosen=candidates[0][1] if candidates and candidates[0][0]>0 else None
            assignments.append({"work_id":w.get("work_id"),"agent_id":chosen.get("agent_id") if chosen else None})
            if chosen: chosen["load"]=min(1,float(chosen.get("load",0))+.25)
        return assignments
