class AdaptiveBackoff:
    """830: stronger backoff for repeated throttling."""

    def seconds(self, failure_kind, attempts):
        attempts = max(0, int(attempts))
        base = 60 if failure_kind == "rate_limited" else 20
        if failure_kind == "timeout":
            base = 15
        return min(3600, base * (2 ** attempts))
