from datetime import datetime, timezone

class ProgressReporter:
    def event(self, stage, **details):
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "details": details,
        }
