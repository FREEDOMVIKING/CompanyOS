class RecoveryPolicy:
    RETRYABLE = {
        "timeout",
        "temporary_provider_failure",
        "transient_network_error",
        "execution_failure",
    }

    def evaluate(self, classification):
        kind = (classification or {}).get("kind")
        return {
            "retry": kind in self.RETRYABLE,
            "max_attempts": 2 if kind in self.RETRYABLE else 0,
            "backoff": "exponential" if kind in self.RETRYABLE else "none"
        }
