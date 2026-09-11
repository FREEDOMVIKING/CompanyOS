class CrashRecovery:
    """554: classify service failures and recovery action."""

    def decide(self, failures, max_failures):
        failures = int(failures)
        if failures <= 0:
            return {"action":"continue"}
        if failures < int(max_failures):
            return {"action":"backoff_and_retry"}
        return {"action":"halt_for_review"}
