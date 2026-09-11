class LiveIntegrationObservability:
    def summarize(self, attempts):
        total=len(attempts or [])
        success=sum(1 for x in attempts or [] if x.get("success"))
        failures=total-success
        return {
            "total":total,
            "success":success,
            "failures":failures,
            "success_rate":round(success/max(1,total),3),
            "healthy":failures==0
        }
