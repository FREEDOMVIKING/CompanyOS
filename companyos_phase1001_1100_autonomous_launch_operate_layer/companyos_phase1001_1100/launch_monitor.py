class LaunchMonitor:
    """1021-1028: launch health and KPI monitor."""
    def evaluate(self, metrics):
        m=metrics or {}
        error=float(m.get("error_rate",0))
        availability=float(m.get("availability",1))
        latency=float(m.get("p95_latency_ms",0))
        healthy=error<0.05 and availability>=0.99 and (latency==0 or latency<2000)
        return {
            "healthy":healthy,
            "error_rate":error,
            "availability":availability,
            "p95_latency_ms":latency,
            "status":"healthy" if healthy else "degraded",
        }
