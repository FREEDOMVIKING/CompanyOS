class VentureBuildIntake:
    """417: admit only complete, validated venture packets into autonomous building."""

    REQUIRED = ("venture_id","brief","mvp_scope","architecture","task_graph","quality_gates","kpis")

    def accept(self, packet):
        missing = [k for k in self.REQUIRED if not packet.get(k)]
        allowed = bool(packet.get("success")) and not missing
        return {
            "accepted": allowed,
            "missing": missing,
            "reason": "venture_packet_complete" if allowed else "venture_packet_incomplete",
        }
