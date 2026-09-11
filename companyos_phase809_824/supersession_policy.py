class SupersessionPolicy:
    """818: decide when old research mission can be retired after promotion."""

    def decide(self, mission, promoted):
        return {
            "retire_original": bool(promoted),
            "reason": "superseded_by_validation" if promoted else "retain_for_research",
            "mission_id": (mission or {}).get("mission_id"),
        }
