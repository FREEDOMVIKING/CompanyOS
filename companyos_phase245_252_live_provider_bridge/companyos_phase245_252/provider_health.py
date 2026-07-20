from __future__ import annotations
import time

class ProviderHealth:
    """250: track provider health for autonomous retry/backoff decisions."""

    def assess(self, probe_result, latency_seconds=None):
        ok = bool(probe_result.get("success"))
        latency = float(latency_seconds or 0)
        return {
            "healthy": ok,
            "latency_seconds": round(latency, 3),
            "recommended_action": "use_provider" if ok else "retry_or_failover",
        }
