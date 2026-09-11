from pathlib import Path
from .mission_executor import MissionExecutor
from .outcome_bridge import OutcomeBridge
from .lifecycle_bridge import LifecycleBridge
from .learning_bridge import LearningBridge
from .context_bus import ContextBus
from companyos_phase761_776 import CEOResearchRuntimeBridge
from companyos_phase793_808 import CEOResearchExecutionBridge

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
        # PHASE793_808_LIVE_RESEARCH_INTEGRATION
        live_research = None
        if mission.get("mission_type") == "research":
            live_research = CEOResearchExecutionBridge(Path.home() / "companyos").process(
                mission,
                executed.get("result") or {},
            )

        research_quality = None
        if mission.get("mission_type") == "research":
            providers = [
                {"name":"github","availability":0.8,"recent_failures":0},
                {"name":"hacker_news","availability":0.9,"recent_failures":0},
                {"name":"public_web","availability":0.95,"recent_failures":0},
                {"name":"local_cache","availability":1.0,"recent_failures":0},
            ]
            research_quality = CEOResearchRuntimeBridge(Path.home() / "companyos").evaluate(
                mission, executed.get("result") or {}, providers
            )

        venture_id = (
            (mission.get("context") or {}).get("venture_id")
            or (mission.get("context") or {}).get("venture_record",{}).get("venture_id")
        )

        if not venture_id:
            return {
                "success": executed["success"],
                "status": "closed_loop_cycle_no_venture_context",
                "execution": executed,
            "live_research": live_research,
                "venture_id": None,
            }

        outcome = self.outcomes.normalize(executed["result"])
        if research_quality:
            outcome.update(research_quality.get("lifecycle_evidence") or {})
        lifecycle = self.lifecycle.apply(venture_id, outcome)
        learning = self.learning.apply(venture_id, lifecycle, outcome)

        return {
            "success": bool(executed["success"]),
            "status": "closed_loop_cycle_completed",
            "venture_id": venture_id,
            "execution": executed,
            "research_quality": research_quality,
            "outcome": outcome,
            "lifecycle": lifecycle,
            "learning": learning,
            "next_mission": learning.get("rewritten_mission") or lifecycle.get("next_mission"),
        }
