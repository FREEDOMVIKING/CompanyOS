from __future__ import annotations
import json, time
from dataclasses import dataclass, asdict
from pathlib import Path

from companyos.runtime.autonomous_goal_scheduler import AutonomousGoalScheduler
from companyos.runtime.autonomous_ceo_runtime_service import AutonomousCEORuntimeService

@dataclass
class ContinuousGoalRuntimeState:
    running: bool = False
    ready: bool = False
    cycles: int = 0
    goals_processed: int = 0
    idle_cycles: int = 0
    consecutive_failures: int = 0
    last_reason: str = "not_started"
    last_orchestration_id: str | None = None
    updated_at_unix: float = 0.0

class ContinuousGoalRuntime:
    """
    Bounded autonomous loop joining Phase 103 durable goal intake to the
    Phase 101 CEO runtime. This layer does not itself perform external actions,
    sign transactions, or broadcast transactions.
    """
    def __init__(self, interval_seconds: int = 10, max_failures: int = 5):
        self.interval_seconds = max(1, int(interval_seconds))
        self.max_failures = max(1, int(max_failures))
        self.scheduler = AutonomousGoalScheduler()
        self.ceo_runtime = AutonomousCEORuntimeService(interval_seconds=self.interval_seconds)
        self.runtime_root = Path.home() / ".companyos_runtime"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.runtime_root / "continuous_goal_runtime_state.json"
        self.stop_path = self.runtime_root / "continuous_goal_runtime.stop"

    def save(self, state):
        state.updated_at_unix = time.time()
        tmp = self.state_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(asdict(state), indent=2, sort_keys=True) + "\n")
        tmp.replace(self.state_path)

    def load(self):
        if not self.state_path.exists():
            return ContinuousGoalRuntimeState()
        return ContinuousGoalRuntimeState(**json.loads(self.state_path.read_text()))

    def cycle(self, state):
        try:
            result = self.scheduler.process_next()
            state.cycles += 1
            if result.processed:
                state.goals_processed += 1
                state.last_orchestration_id = result.orchestration_id
                state.last_reason = result.reason
            else:
                state.idle_cycles += 1
                state.last_reason = result.reason

            ceo_state = self.ceo_runtime.startup()
            self.ceo_runtime.cycle(ceo_state)

            state.running = True
            state.ready = True
            state.consecutive_failures = 0
        except Exception as exc:
            state.cycles += 1
            state.consecutive_failures += 1
            state.last_reason = f"{type(exc).__name__}:{exc}"
            state.ready = False
        self.save(state)
        return state

    def run(self, max_cycles=0):
        self.stop_path.unlink(missing_ok=True)
        state = self.load()
        state.running = True
        state.ready = True
        self.save(state)
        completed = 0
        while not self.stop_path.exists():
            state = self.cycle(state)
            completed += 1
            if state.consecutive_failures >= self.max_failures:
                state.running = False
                state.ready = False
                state.last_reason = "max_failures_reached"
                self.save(state)
                return state
            if max_cycles and completed >= max_cycles:
                break
            time.sleep(self.interval_seconds)
        state.running = False
        if self.stop_path.exists():
            state.last_reason = "stopped_by_user"
        self.save(state)
        return state

    def request_stop(self):
        self.stop_path.write_text("stop\n")
