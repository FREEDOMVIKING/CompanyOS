from __future__ import annotations
from pathlib import Path

from companyos_phase253_260 import BuilderBridge

from .health_observer import HealthObserver
from .improvement_planner import ImprovementPlanner
from .capability_mapper import CapabilityMapper
from .improvement_mission import ImprovementMission
from .verification_policy import VerificationPolicy
from .learning_recorder import LearningRecorder

class AutonomousImprover:
    """267: observe -> choose -> self-build -> verify -> learn."""

    def __init__(self, project_root, builder=None):
        self.root = Path(project_root).resolve()
        self.observer = HealthObserver(self.root)
        self.planner = ImprovementPlanner()
        self.mapper = CapabilityMapper()
        self.missions = ImprovementMission()
        self.verification = VerificationPolicy()
        self.learning = LearningRecorder(self.root)
        self.builder = builder or BuilderBridge(self.root)

    def run_once(self):
        observation = self.observer.observe()
        proposal = self.planner.propose(observation)
        mapped = self.mapper.map(proposal)
        mission = self.missions.create(mapped)
        targeted_test = f"tests/test_{mapped['module_name']}.py"

        result = self.builder.build(
            capability=mapped["capability"],
            module_name=mapped["module_name"],
            mission=mission,
            targeted_test=targeted_test,
        )

        verification = self.verification.evaluate(result)
        learning = self.learning.record(
            proposal,
            mission,
            result,
            verification,
        )

        return {
            "success": bool(result.get("success")) and verification.get("approved"),
            "status": (
                "autonomous_improvement_completed"
                if result.get("success") and verification.get("approved")
                else "autonomous_improvement_not_promoted"
            ),
            "observation": observation,
            "proposal": proposal,
            "mapped": mapped,
            "mission": mission,
            "build_result": result,
            "verification": verification,
            "learning": learning,
        }
