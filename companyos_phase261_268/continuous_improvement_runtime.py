from __future__ import annotations
from pathlib import Path
from .health_observer import HealthObserver
from .improvement_planner import ImprovementPlanner

class ContinuousImprovementRuntime:
    """268: runtime status surface for autonomous internal improvement."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()

    def status(self):
        observation = HealthObserver(self.root).observe()
        proposal = ImprovementPlanner().propose(observation)
        return {
            "success": True,
            "status": "phase268_continuous_improvement_runtime_ready",
            "observation": observation,
            "next_internal_improvement": proposal,
            "autonomous_improvement_loop_connected": True,
            "external_actions_enabled_by_this_loop": False,
            "financial_actions_enabled_by_this_loop": False,
            "autonomy_mode": "high",
        }
