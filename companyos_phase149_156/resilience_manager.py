class ResilienceManager:
    """154: recover from routine failures without stopping the company loop."""
    SAFE={"retry","restart_worker","restore_last_good_state","requeue","fallback_provider"}
    def respond(self, failure):
        action=str(failure.get("recommended_action","retry"))
        safe=action in self.SAFE and not failure.get("destructive",False)
        return {"action":action if safe else "isolate_and_escalate","autonomous":safe,"continue_operation":safe}
