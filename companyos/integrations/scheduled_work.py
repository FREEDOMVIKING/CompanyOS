class ScheduledWorkPlanner:
    def plan(self, items):
        out=[]
        for x in items or []:
            out.append({
                "name":x.get("name"),
                "cadence":x.get("cadence","daily"),
                "task_type":x.get("task_type","operations"),
                "enabled":x.get("enabled",True)
            })
        return out
