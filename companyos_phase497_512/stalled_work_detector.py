class StalledWorkDetector:
    """506: detect missions that keep retrying without progress."""

    def detect(self, missions, attempt_threshold=3):
        return [
            m for m in missions
            if int(m.get("attempts",0)) >= int(attempt_threshold)
            and m.get("status") not in ("completed","cancelled")
        ]
