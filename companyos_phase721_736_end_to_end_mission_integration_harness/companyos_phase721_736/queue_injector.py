from companyos_phase481_496 import MissionQueue

class QueueInjector:
    """722: safely inject a controlled mission into the persistent queue."""

    def __init__(self, root):
        self.queue=MissionQueue(root)

    def inject(self, mission):
        missions=self.queue.load()
        ids={m.get("mission_id") for m in missions}
        if mission.get("mission_id") not in ids:
            missions.append(mission)
            self.queue.save(missions)
            inserted=True
        else:
            inserted=False
        return {
            "inserted":inserted,
            "mission_id":mission.get("mission_id"),
            "queue_size":len(missions),
        }
