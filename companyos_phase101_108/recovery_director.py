class RecoveryDirector:
    """107: bounded incident recovery and escalation."""
    def direct(self,incident):
        severity=str(incident.get("severity","low"))
        reversible=bool(incident.get("reversible",True))
        if severity=="critical" or not reversible:
            return {"action":"contain_and_escalate","automatic_destructive_action":False,"requires_attention":True}
        return {"action":"retry_or_rollback_safely","automatic_destructive_action":False,"requires_attention":False}
