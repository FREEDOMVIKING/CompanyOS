class LongRunningScheduler:
    def expand(self, schedules):
        jobs=[]
        for s in schedules or []:
            if not s.get("enabled",True): continue
            jobs.append({
                "name":s.get("name"),
                "cadence":s.get("cadence","daily"),
                "capability":s.get("capability","operations"),
                "priority":int(s.get("priority",5))
            })
        return sorted(jobs,key=lambda x:x["priority"],reverse=True)
