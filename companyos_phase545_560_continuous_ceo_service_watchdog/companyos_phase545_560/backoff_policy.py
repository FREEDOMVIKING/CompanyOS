class BackoffPolicy:
    """551: bounded failure backoff."""

    def delay(self, consecutive_failures, base_seconds=30):
        failures = max(0, int(consecutive_failures))
        return min(3600, int(base_seconds) * (2 ** min(failures, 6)))
