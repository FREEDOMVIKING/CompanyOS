class RetryPolicy:
    def decision(self, diagnosis, attempts):
        attempts = int(attempts or 0)
        kind = (diagnosis or {}).get("kind")
        limits = {
            "missing_input": 1,
            "transient_failure": 2,
            "execution_failure": 1,
        }
        max_attempts = limits.get(kind, 0)
        return {
            "retry": attempts < max_attempts,
            "max_attempts": max_attempts,
            "next_attempt": attempts + 1 if attempts < max_attempts else attempts,
            "backoff_seconds": 0 if kind == "missing_input" else min(30, 2 ** attempts),
        }
