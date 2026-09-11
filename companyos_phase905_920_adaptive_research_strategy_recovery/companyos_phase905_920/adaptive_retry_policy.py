class AdaptiveRetryPolicy:
    """913: retry only when strategy materially changes."""
    def decide(self, previous_query, new_query, previous_providers, new_providers, attempts, max_attempts=3):
        changed=(str(previous_query)!=str(new_query)) or (list(previous_providers or [])!=list(new_providers or []))
        if int(attempts)>=int(max_attempts):
            return {"retry":False,"reason":"adaptive_retry_limit_reached"}
        if not changed:
            return {"retry":False,"reason":"strategy_unchanged"}
        return {"retry":True,"reason":"strategy_changed"}
