class JobDispatcher:
    def dispatch(self, jobs, workers):
        assignments=[]
        workers=[dict(w) for w in workers or []]
        for job in jobs or []:
            cap=job.get("capability")
            candidates=[w for w in workers if w.get("status")=="idle" and (not cap or cap in w.get("capabilities",[]))]
            if not candidates:
                assignments.append({"job":job,"worker":None,"status":"queued"})
                continue
            candidates.sort(key=lambda w:float(w.get("reliability",0.5)),reverse=True)
            chosen=candidates[0]
            chosen["status"]="busy"
            assignments.append({"job":job,"worker":chosen.get("worker_id"),"status":"assigned"})
        return assignments
