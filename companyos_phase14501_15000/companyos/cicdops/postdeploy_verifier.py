class PostDeployVerifier:
    def verify(self, smoke_ok, health_ok, error_rate_ok=True, latency_ok=True):
        checks = {
            "smoke_ok": bool(smoke_ok),
            "health_ok": bool(health_ok),
            "error_rate_ok": bool(error_rate_ok),
            "latency_ok": bool(latency_ok),
        }
        return {"passed": all(checks.values()), "checks": checks}
