from __future__ import annotations
from pathlib import Path

from .run_lock import RunLock
from .cycle_budget import CycleBudget
from .cycle_scheduler import CycleScheduler
from .supervised_improver import SupervisedImprover
from .failure_tracker import FailureTracker

class ContinuousSupervisor:
    """283: sequential continuous internal-improvement supervisor."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.lock = RunLock(self.root)
        self.budget = CycleBudget()
        self.scheduler = CycleScheduler()
        self.supervised = SupervisedImprover(self.root)
        self.failures = FailureTracker(self.root)

    def run(self):
        acquired = self.lock.acquire()
        if not acquired.get("acquired"):
            return {"success": False, "status": "supervisor_locked", "lock": acquired}

        cycles = []
        limits = self.budget.limits()

        try:
            for cycle_number in range(1, limits["max_cycles_per_run"] + 1):
                current = self.failures.state()
                if int(current.get("consecutive_failures", 0)) >= limits["max_consecutive_failures"]:
                    return {
                        "success": False,
                        "status": "supervisor_stopped_repeated_failures",
                        "cycles": cycles,
                        "failure_state": current,
                    }

                outcome = self.supervised.run_cycle(cycle_number)
                cycles.append(outcome)

                if cycle_number < limits["max_cycles_per_run"]:
                    self.scheduler.wait(limits["cooldown_seconds"])

            overall = all(bool(x["result"].get("success")) for x in cycles)
            return {
                "success": overall,
                "status": "continuous_improvement_run_completed",
                "cycles": cycles,
                "limits": limits,
            }
        finally:
            self.lock.release()
