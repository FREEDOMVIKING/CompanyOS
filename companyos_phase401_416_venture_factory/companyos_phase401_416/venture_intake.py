class VentureIntake:
    """401: accept only sufficiently validated opportunities into the venture factory."""

    ALLOWED = {"go_to_mvp", "approved_for_mvp", "validated"}

    def accept(self, validation):
        decision = validation.get("decision", {})
        if isinstance(decision, dict):
            decision = decision.get("decision")
        accepted = decision in self.ALLOWED
        return {
            "accepted": accepted,
            "decision": decision,
            "reason": "validated_opportunity" if accepted else "validation_gate_not_met",
        }
