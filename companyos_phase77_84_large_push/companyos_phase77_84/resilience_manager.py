class ResilienceManager:
    """83: classify failures and produce bounded recovery plans."""
    def plan(self,failure):
        kind=str(failure.get("kind","unknown"))
        attempts=int(failure.get("attempts",0))
        if attempts>=3:return {"action":"escalate","retry":False,"requires_attention":True}
        if kind in {"timeout","temporary_dependency","rate_limit"}:
            return {"action":"retry_with_backoff","retry":True,"requires_attention":False}
        return {"action":"isolate_and_review","retry":False,"requires_attention":True}
