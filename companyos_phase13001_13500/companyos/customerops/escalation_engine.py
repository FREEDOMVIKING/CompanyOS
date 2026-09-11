class EscalationEngine:
    def decide(self, ticket):
        urgent=ticket.get("priority")=="urgent"
        legal=bool(ticket.get("legal_risk")); security=bool(ticket.get("security_risk"))
        return {"ticket_id":ticket.get("ticket_id"),"escalate":urgent or legal or security,
                "reason":"protected_or_urgent" if urgent or legal or security else "standard"}
