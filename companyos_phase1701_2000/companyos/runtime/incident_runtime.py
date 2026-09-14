class RuntimeIncidentManager:
    def classify(self, error):
        text=str(error).lower()
        if "timeout" in text: kind="transient_timeout"
        elif "rate" in text and "limit" in text: kind="rate_limited"
        elif "memory" in text: kind="resource_pressure"
        else: kind="unknown_runtime_failure"
        return {"kind":kind,"recoverable":kind!="unknown_runtime_failure"}

    def recovery_action(self, classified):
        kind=classified.get("kind")
        return {
            "transient_timeout":"retry_with_backoff",
            "rate_limited":"switch_provider_or_delay",
            "resource_pressure":"reduce_concurrency",
            "unknown_runtime_failure":"safe_stop_and_review",
        }.get(kind,"safe_stop_and_review")
