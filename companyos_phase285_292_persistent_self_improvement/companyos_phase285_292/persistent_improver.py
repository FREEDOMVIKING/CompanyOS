from __future__ import annotations
import time
from pathlib import Path

from companyos_phase277_284 import ContinuousSupervisor, FailureTracker
from .state_store import ImprovementStateStore
from .cycle_journal import CycleJournal
from .pause_policy import PausePolicy
from .adaptive_scheduler import AdaptiveScheduler

class PersistentImprover:
    """290: persistent observe/build/verify/learn loop with durable resume state."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.supervisor = ContinuousSupervisor(self.root)
        self.failures = FailureTracker(self.root)
        self.state_store = ImprovementStateStore(self.root)
        self.journal = CycleJournal(self.root)
        self.pause_policy = PausePolicy()
        self.scheduler = AdaptiveScheduler()

    def run(self, max_rounds=1, sleep_between=False):
        state = self.state_store.load()
        rounds = []

        for idx in range(1, int(max_rounds) + 1):
            pause = self.pause_policy.evaluate(
                state,
                self.failures.state(),
                max_failures=3,
            )
            if pause["pause"]:
                self.journal.append("paused", pause)
                return {
                    "success": False,
                    "status": "persistent_improvement_paused",
                    "reason": pause["reason"],
                    "rounds": rounds,
                    "state": state,
                }

            self.journal.append("round_started", {"round": idx})
            result = self.supervisor.run()
            rounds.append(result)

            state["cycles_completed"] = int(state.get("cycles_completed", 0)) + 1
            state["last_status"] = result.get("status")
            state["last_success"] = bool(result.get("success"))

            try:
                cycles = result.get("cycles") or []
                if cycles:
                    proposal = cycles[-1]["result"].get("proposal") or {}
                    state["last_capability"] = proposal.get("improvement")
            except Exception:
                pass

            self.state_store.save(state)
            self.journal.append("round_completed", {
                "round": idx,
                "success": bool(result.get("success")),
                "status": result.get("status"),
            })

            if sleep_between and idx < int(max_rounds):
                time.sleep(self.scheduler.next_delay(bool(result.get("success"))))

        return {
            "success": all(bool(x.get("success")) for x in rounds),
            "status": "persistent_improvement_run_completed",
            "rounds": rounds,
            "state": state,
        }
