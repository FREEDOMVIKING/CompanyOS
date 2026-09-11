class LiveExecutionObservability:
    def summarize(self, executions):
        total=len(executions or [])
        complete=sum(1 for x in executions or [] if x.get("status")=="complete")
        failed=sum(1 for x in executions or [] if x.get("status")=="failed")
        return {
            "total":total,
            "complete":complete,
            "failed":failed,
            "success_rate":round(complete/max(1,total),3),
            "healthy":failed==0
        }
