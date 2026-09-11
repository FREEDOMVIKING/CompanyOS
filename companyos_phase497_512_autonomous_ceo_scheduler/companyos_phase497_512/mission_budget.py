import os

class MissionBudget:
    """503: bounded scheduler execution budget."""

    def limits(self):
        return {
            "max_new_missions_per_tick": max(1, int(os.getenv("COMPANYOS_MAX_NEW_MISSIONS_PER_TICK", "5"))),
            "max_execute_per_tick": max(1, int(os.getenv("COMPANYOS_MAX_EXECUTE_PER_TICK", "3"))),
            "max_queue_size": max(10, int(os.getenv("COMPANYOS_MAX_MISSION_QUEUE_SIZE", "100"))),
        }
