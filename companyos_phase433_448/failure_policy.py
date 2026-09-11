class FailurePolicy:
    """438: classify failures and determine response."""

    def decide(self, failures, retries, max_failures=3, max_retries=2):
        failures = int(failures)
        retries = int(retries)
        if failures >= max_failures:
            return {"action":"pause","reason":"failure_threshold_reached"}
        if retries < max_retries:
            return {"action":"retry","reason":"retry_budget_available"}
        return {"action":"escalate","reason":"retry_budget_exhausted"}
