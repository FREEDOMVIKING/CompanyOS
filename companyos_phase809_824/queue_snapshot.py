class QueueSnapshot:
    """809: summarize queue state before/after recovery."""

    def build(self, missions):
        missions = list(missions or [])
        return {
            "count": len(missions),
            "deferred": sum(1 for m in missions if m.get("status") == "deferred"),
            "research": sum(1 for m in missions if m.get("mission_type") == "research"),
            "validation": sum(1 for m in missions if m.get("mission_type") == "validation"),
            "failed": sum(1 for m in missions if m.get("status") == "failed"),
        }
