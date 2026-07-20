from __future__ import annotations
from pathlib import Path
from .cycle_budget import CycleBudget
from .failure_tracker import FailureTracker

class SupervisorRuntime:
    """284: status surface for continuous autonomous improvement."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()

    def status(self):
        return {
            "success": True,
            "status": "phase284_continuous_supervisor_ready",
            "limits": CycleBudget().limits(),
            "failure_state": FailureTracker(self.root).state(),
            "continuous_internal_improvement": True,
            "overlap_protection": True,
            "repeated_failure_breaker": True,
            "verification_gates_preserved": True,
            "external_actions_enabled_by_supervisor": False,
            "financial_actions_enabled_by_supervisor": False,
            "autonomy_mode": "high",
        }
