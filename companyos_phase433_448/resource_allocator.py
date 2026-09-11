class ResourceAllocator:
    """435: allocate bounded build capacity across ventures."""

    def allocate(self, ventures, max_active=2):
        ordered = sorted(
            ventures,
            key=lambda v: float(v.get("priority", 0.5)),
            reverse=True,
        )
        active = ordered[:max(1, int(max_active))]
        waiting = ordered[len(active):]
        return {"active": active, "waiting": waiting}
