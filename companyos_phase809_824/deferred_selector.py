class DeferredSelector:
    """810: select retryable deferred research missions."""

    def select(self, missions):
        return [
            m for m in (missions or [])
            if m.get("mission_type") == "research"
            and m.get("status") == "deferred"
            and not m.get("blocked_on")
        ]
