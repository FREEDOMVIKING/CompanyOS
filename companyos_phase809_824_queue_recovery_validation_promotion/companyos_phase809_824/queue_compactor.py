from .mission_deduplicator import MissionDeduplicator
from .test_mission_retirement import TestMissionRetirement

class QueueCompactor:
    """819: remove retired tests and duplicate missions."""

    def compact(self, missions):
        active, retired = [], []
        for m in missions or []:
            if TestMissionRetirement().classify(m)["retire"]:
                retired.append(m)
            else:
                active.append(m)

        deduped = MissionDeduplicator().dedupe(active)
        retired.extend(deduped["dropped"])
        return {
            "missions": deduped["kept"],
            "retired": retired,
        }
