class MissionDeduper:
    """502: prevent duplicate queued work."""

    def unique(self, missions):
        out, seen = [], set()
        for mission in missions:
            key = mission.get("mission_id")
            if key in seen:
                continue
            seen.add(key)
            out.append(mission)
        return out
