from .mission_executor import MissionExecutor
from .outcome_bridge import OutcomeBridge
from .lifecycle_bridge import LifecycleBridge
from .learning_bridge import LearningBridge
from .context_bus import ContextBus

class ClosedLoopCycle:
    """716: mission -> outcome -> lifecycle -> learning -> next mission."""

    def __init__(self, root):
        self.executor = MissionExecutor(root)
        self.outcomes = OutcomeBridge()
        self.lifecycle = LifecycleBridge(root)
        self.learning = LearningBridge(root)
        self.context = ContextBus()

    def run(self, mission):
        executed = self.executor.execute(mission)
        venture_id = (
            (mission.get("context") or {}).get("venture_id")
            or (mission.get("context") or {}).get("venture_record",{}).get("venture_id")
        )

        if not venture_id:
            return {
                "success": executed["success"],
                "status": "closed_loop_cycle_no_venture_context",
                "execution": executed,
                "venture_id": None,
            }

        outcome = self.outcomes.normalize(executed["result"])
        lifecycle = self.lifecycle.apply(venture_id, outcome)
        learning = self.learning.apply(venture_id, lifecycle, outcome)

        return {
            "success": bool(executed["success"]),
            "status": "closed_loop_cycle_completed",
            "venture_id": venture_id,
            "execution": executed,
            "outcome": outcome,
            "lifecycle": lifecycle,
            "learning": learning,
            "next_mission": learning.get("rewritten_mission") or lifecycle.get("next_mission"),
        }
