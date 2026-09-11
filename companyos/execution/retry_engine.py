class AdaptiveRetryEngine:
    def decide(self, error_kind, attempts, max_attempts=4):
        attempts=int(attempts)
        if attempts>=int(max_attempts):
            return {"retry":False,"action":"escalate_or_safe_stop"}
        mapping={
            "timeout":"retry_with_backoff",
            "rate_limit":"delay_or_switch_provider",
            "transient":"retry",
            "bad_input":"repair_input_then_retry",
        }
        return {"retry":error_kind in mapping,"action":mapping.get(error_kind,"safe_diagnose")}
