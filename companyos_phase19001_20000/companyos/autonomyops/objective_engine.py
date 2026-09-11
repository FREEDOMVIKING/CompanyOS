class ObjectiveEngine:
    DEFAULT_OBJECTIVES = [
        "Discover the highest-value business opportunity available from current evidence.",
        "Improve the strongest existing venture's revenue, retention, or operating efficiency.",
        "Reduce the largest unresolved operational risk without external side effects.",
        "Generate and validate the next bounded product or growth experiment."
    ]

    def choose(self, recent_memory=None):
        recent_memory = recent_memory or []
        completed = {
            str((r.get("payload") or {}).get("objective","")).strip()
            for r in recent_memory
            if isinstance(r, dict)
        }
        for obj in self.DEFAULT_OBJECTIVES:
            if obj not in completed:
                return obj
        return self.DEFAULT_OBJECTIVES[0]
