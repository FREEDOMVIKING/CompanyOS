from companyos_phase481_496 import MissionQueue

class QueueProbe:
    """728: inspect persistent mission queue."""

    def __init__(self, root):
        self.queue=MissionQueue(root)

    def inspect(self):
        missions=self.queue.load()
        return {
            "count":len(missions),
            "mission_ids":[m.get("mission_id") for m in missions],
            "missions":missions,
        }
