class ExecutionMetrics:
    def summarize(self, assignments, recoveries, services):
        assigned=sum(1 for x in assignments or [] if x.get("status")=="assigned")
        queued=sum(1 for x in assignments or [] if x.get("status")=="queued")
        restarts=sum(1 for x in services or [] if x.get("action")=="restart")
        return {
            "assigned":assigned,
            "queued":queued,
            "recoveries":len(recoveries or []),
            "service_restarts":restarts,
            "healthy":queued==0 and restarts==0,
        }
