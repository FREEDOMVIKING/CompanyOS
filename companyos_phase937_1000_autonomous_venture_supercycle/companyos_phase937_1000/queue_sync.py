class QueueSync:
    """995: queue handoff normalization across lifecycle stages."""
    def sync(self, current_queue, next_mission=None, retire_ids=None):
        retire_ids=set(retire_ids or [])
        q=[m for m in (current_queue or []) if m.get("mission_id") not in retire_ids]
        if next_mission:
            if not any(m.get("mission_id")==next_mission.get("mission_id") for m in q):
                q.append(next_mission)
        return q
