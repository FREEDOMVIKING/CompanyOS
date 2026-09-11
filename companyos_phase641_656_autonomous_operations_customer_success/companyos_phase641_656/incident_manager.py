class IncidentManager:
    """646: classify operational incidents and required response."""

    def classify(self, incident):
        impact=int(incident.get("affected_customers",0))
        core=bool(incident.get("core_service_down"))
        data_risk=bool(incident.get("data_integrity_risk"))
        if core or data_risk or impact>=50:
            severity="critical"
        elif impact>=10:
            severity="high"
        elif impact>0:
            severity="medium"
        else:
            severity="low"
        return {
            "severity":severity,
            "requires_immediate_response":severity in ("critical","high"),
            "requires_postmortem":severity=="critical",
        }
