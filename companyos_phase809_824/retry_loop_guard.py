class RetryLoopGuard:
    """811: prevent endless retries."""

    def evaluate(self, mission, max_attempts=4):
        attempts = int((mission or {}).get("attempts", 0))
        return {
            "allowed": attempts < int(max_attempts),
            "attempts": attempts,
            "max_attempts": int(max_attempts),
            "reason": "retry_allowed" if attempts < int(max_attempts) else "retry_limit_reached",
        }
