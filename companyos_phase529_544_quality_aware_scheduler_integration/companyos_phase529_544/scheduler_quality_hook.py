from companyos_phase481_496 import MissionQueue

class SchedulerQualityHook:
    """538: inject quality-derived missions into persistent mission queue."""

    def __init__(self, root):
        self.queue = MissionQueue(root)

    def inject(self, missions):
        existing = self.queue.load()
        existing_ids = {m.get("mission_id") for m in existing}
        added = []
        for m in missions:
            if m.get("mission_id") in existing_ids:
                continue
            existing.append(m)
            added.append(m)
            existing_ids.add(m.get("mission_id"))
        self.queue.save(existing)
        return {"added":added,"queue_size":len(existing)}
