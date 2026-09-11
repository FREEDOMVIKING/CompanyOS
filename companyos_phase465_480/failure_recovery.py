class FailureRecovery:
    """476: bounded recovery policy for unified CEO cycle failures."""

    def decide(self, failures, stage):
        failures = int(failures)
        if failures <= 0:
            return {"action":"continue","stage":stage}
        if failures < 3:
            return {"action":"retry_stage","stage":stage}
        return {"action":"pause_cycle","stage":stage}
