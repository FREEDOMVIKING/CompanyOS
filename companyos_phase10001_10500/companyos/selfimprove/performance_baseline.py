class PerformanceBaseline:
    def build(self, metrics):
        return {
            "latency":float(metrics.get("latency",0)),
            "success_rate":float(metrics.get("success_rate",0)),
            "cost_per_cycle":float(metrics.get("cost_per_cycle",0)),
            "recovery_rate":float(metrics.get("recovery_rate",0)),
            "throughput":float(metrics.get("throughput",0)),
        }
