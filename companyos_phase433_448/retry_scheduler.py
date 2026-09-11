class RetryScheduler:
    """439: bounded exponential retry schedule."""

    def delay_seconds(self, retries):
        retries = max(0, int(retries))
        return min(3600, 30 * (2 ** min(retries, 6)))
