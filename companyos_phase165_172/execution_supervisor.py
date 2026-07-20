class ExecutionSupervisor:
    """168: supervise autonomous work, retry recoverable failures, and advance successes."""
    def supervise(self, jobs):
        out=[]
        for j in jobs:
            status=j.get("status","queued"); attempts=int(j.get("attempts",0))
            if status=="failed" and attempts<3 and not j.get("destructive_failure",False):
                action="retry"
            elif status=="completed":
                action="advance_dependency"
            elif status=="running":
                action="continue"
            else:
                action="queue_or_review"
            out.append({**j,"supervisor_action":action,"autonomous":action in {"retry","advance_dependency","continue"}})
        return out
