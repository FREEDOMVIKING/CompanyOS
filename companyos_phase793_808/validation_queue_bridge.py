class ValidationQueueBridge:
    """804: normalize validation handoff for mission queue insertion."""

    def build(self, handoff):
        if not handoff:
            return None
        if handoff.get("mission_type") != "validation":
            return None
        if not handoff.get("mission_id"):
            source = handoff.get("source_mission_id") or "unknown"
            handoff = dict(handoff)
            handoff["mission_id"] = f"{source}_validation"
        handoff.setdefault("attempts", 0)
        handoff.setdefault("blocked_on", [])
        handoff.setdefault("status", "queued")
        return handoff
