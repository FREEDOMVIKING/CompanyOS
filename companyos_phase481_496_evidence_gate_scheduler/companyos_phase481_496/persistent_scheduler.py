from .mission_queue import MissionQueue
from .mission_scheduler import MissionScheduler
from .mission_orchestrator import MissionOrchestrator

class PersistentScheduler:
    """495: bounded persistent CEO mission scheduler."""

    def __init__(self, root):
        self.queue = MissionQueue(root)
        self.scheduler = MissionScheduler()
        self.orchestrator = MissionOrchestrator(root)

    def run_once(self, max_missions=3):
        missions = self.queue.load()
        ordered = self.scheduler.order(missions)
        ready = ordered["ready"][:max(1,int(max_missions))]
        results = []

        for mission in ready:
            result = self.orchestrator.run(mission)
            results.append({"mission":mission,"result":result})

            mission["attempts"] = int(mission.get("attempts",0)) + 1
            mission["status"] = "completed" if result.get("success") else "failed"

        remaining = [
            m for m in missions
            if m.get("status") not in ("completed",)
        ]
        self.queue.save(remaining)

        return {
            "success":True,
            "status":"persistent_mission_scheduler_run_complete",
            "executed_count":len(results),
            "remaining_count":len(remaining),
            "blocked_count":len(ordered["blocked"]),
            "results":results,
        }
