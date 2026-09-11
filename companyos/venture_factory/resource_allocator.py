class ResourceAllocator:
    def allocate(self, ventures, budget=10000, worker_slots=10):
        active=[v for v in ventures or [] if v.get("decision") not in ("RETIRE","STOP")]
        total=sum(max(.01,float(v.get("score",0))) for v in active) or 1
        rows=[]
        remaining=int(worker_slots)
        for i,v in enumerate(active):
            share=max(.01,float(v.get("score",0)))/total
            slots=max(1,round(worker_slots*share)) if remaining else 0
            slots=min(slots,remaining); remaining-=slots
            rows.append({"venture_id":v["venture_id"],"budget":round(budget*share,2),"worker_slots":slots})
        return rows
