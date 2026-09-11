from datetime import datetime, timezone

class SchedulerHeartbeat:
    """505: visible scheduler liveness record."""

    def beat(self, queue_size, executed):
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "queue_size": int(queue_size),
            "executed": int(executed),
            "alive": True,
        }
