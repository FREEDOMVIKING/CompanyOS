class MissionScheduler:
    """487: prioritize ready missions while respecting blocked dependencies."""

    def order(self, missions):
        ready = [m for m in missions if not m.get("blocked_on")]
        blocked = [m for m in missions if m.get("blocked_on")]

        ready.sort(
            key=lambda m: (float(m.get("priority",0.5)), -int(m.get("attempts",0))),
            reverse=True,
        )
        blocked.sort(key=lambda m: float(m.get("priority",0.5)), reverse=True)

        return {"ready":ready,"blocked":blocked}
