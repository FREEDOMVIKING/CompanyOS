class ServiceQuality:
    """648: calculate service quality signals."""

    def evaluate(self, metrics):
        uptime=float(metrics.get("uptime",0))
        error_rate=float(metrics.get("error_rate",0))
        success_rate=float(metrics.get("core_workflow_success_rate",0))
        return {
            "uptime":uptime,
            "error_rate":error_rate,
            "core_workflow_success_rate":success_rate,
            "healthy":uptime>=0.99 and error_rate<=0.02 and success_rate>=0.95,
        }
