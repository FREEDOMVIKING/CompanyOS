class VentureHealth:
    """443: summarize venture execution health."""

    def evaluate(self, venture):
        failures = int(venture.get("failures",0))
        blocked = bool(venture.get("blocked_reason"))
        if blocked or failures >= 3:
            level = "critical"
        elif failures > 0:
            level = "warning"
        else:
            level = "healthy"
        return {"level":level,"failures":failures,"blocked":blocked}
