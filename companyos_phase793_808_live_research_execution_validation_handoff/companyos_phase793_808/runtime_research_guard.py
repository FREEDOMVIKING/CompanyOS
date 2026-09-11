class RuntimeResearchGuard:
    """802: only invoke multi-provider collection for research missions."""

    def should_run(self, mission):
        return (
            isinstance(mission, dict)
            and mission.get("mission_type") == "research"
            and bool(mission.get("mission_id"))
        )
