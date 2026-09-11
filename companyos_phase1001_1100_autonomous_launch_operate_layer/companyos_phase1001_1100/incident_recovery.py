class IncidentRecovery:
    """1061-1068: select safe recovery actions."""
    def plan(self, incidents, rollback_ready=True):
        actions=[]
        for incident in (incidents or {}).get("incidents",[]):
            if incident.get("type")=="service_health" and rollback_ready:
                actions.append("rollback_release")
            elif incident.get("type")=="service_health":
                actions.append("degrade_gracefully")
            elif incident.get("type")=="refund_spike":
                actions.append("pause_growth_spend")
            elif incident.get("type")=="chargeback_spike":
                actions.append("freeze_risky_checkout_paths")
        return {"actions":actions,"automatic":True,"requires_approval":False}
