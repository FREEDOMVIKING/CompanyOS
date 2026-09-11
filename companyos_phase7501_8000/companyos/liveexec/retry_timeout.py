class RetryTimeoutPolicy:
    def decide(self, error_kind, attempts, max_attempts=4, timeout_seconds=30):
        attempts=int(attempts)
        retryable=error_kind in {"timeout","rate_limit","transient","provider_unavailable","network"}
        return {
            "retry":retryable and attempts<int(max_attempts),
            "timeout_seconds":int(timeout_seconds),
            "next_action":{
                "timeout":"retry_with_backoff",
                "rate_limit":"delay_or_switch_provider",
                "transient":"retry",
                "provider_unavailable":"switch_provider",
                "network":"retry_with_backoff"
            }.get(error_kind,"stop_and_diagnose")
        }
