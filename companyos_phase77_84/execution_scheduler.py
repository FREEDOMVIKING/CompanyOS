class ExecutionScheduler:
    """80: choose ready internal work by priority and dependencies."""
    def ready(self,tasks,completed=None,limit=10):
        completed=set(completed or [])
        rows=[t for t in tasks if set(t.get("depends_on",[])).issubset(completed) and t.get("status","queued")=="queued"]
        rows.sort(key=lambda x:float(x.get("priority",0)),reverse=True)
        return rows[:max(1,int(limit))]
