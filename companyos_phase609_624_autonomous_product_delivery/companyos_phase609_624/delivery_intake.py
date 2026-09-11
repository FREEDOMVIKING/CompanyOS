class DeliveryIntake:
    """609: admit only validated venture/build contexts into product delivery."""

    REQUIRED = ("venture_id", "brief", "mvp_scope", "quality_gates")

    def evaluate(self, packet):
        missing = [k for k in self.REQUIRED if not packet.get(k)]
        return {
            "accepted": bool(packet.get("success", True)) and not missing,
            "missing": missing,
            "reason": "delivery_context_complete" if not missing else "delivery_context_incomplete",
        }
