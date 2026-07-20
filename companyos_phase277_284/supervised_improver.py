from __future__ import annotations
from pathlib import Path

from companyos_phase261_268 import AutonomousImprover
from .failure_tracker import FailureTracker
from .improvement_history import ImprovementHistory

class SupervisedImprover:
    """282: run one improvement cycle with failure/history accounting."""

    def __init__(self, project_root, improver=None):
        self.root = Path(project_root).resolve()
        self.improver = improver or AutonomousImprover(self.root)
        self.failures = FailureTracker(self.root)
        self.history = ImprovementHistory(self.root)

    def run_cycle(self, cycle_number=1):
        result = self.improver.run_once()
        failure_state = self.failures.record(
            bool(result.get("success")),
            reason=(result.get("verification") or {}).get("reason") or result.get("status"),
        )
        history = self.history.append(cycle_number, result)
        return {
            "result": result,
            "failure_state": failure_state,
            "history": history,
        }
