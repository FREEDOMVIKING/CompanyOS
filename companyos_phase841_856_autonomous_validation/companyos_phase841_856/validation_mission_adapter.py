class ValidationMissionAdapter:
    """841: normalize validation mission context."""
    def adapt(self, mission):
        ctx = dict((mission or {}).get("context") or {})
        packet = dict(ctx.get("research_packet") or {})
        return {
            "mission_id": (mission or {}).get("mission_id"),
            "venture_id": ctx.get("venture_id") or (ctx.get("venture_record") or {}).get("venture_id"),
            "research_packet": packet,
            "research_confidence": float(ctx.get("research_confidence", packet.get("confidence", 0)) or 0),
            "objective": ctx.get("objective") or "validate customer/problem hypothesis",
            "attempts": int((mission or {}).get("attempts", 0)),
            "context": ctx,
        }
