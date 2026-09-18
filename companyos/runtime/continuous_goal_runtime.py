from __future__ import annotations
import json, time
from dataclasses import dataclass, asdict
from pathlib import Path

from companyos.runtime.autonomous_goal_scheduler import AutonomousGoalScheduler
from companyos.runtime.autonomous_ceo_runtime_service import AutonomousCEORuntimeService
from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

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
    execution_dispatched: int = 0
    execution_failures: int = 0
    scheduler_failures: int = 0
    ceo_failures: int = 0

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
        self.execution_loop = AutonomousGoalExecutionLoop()
        self.execution_batch_size = 8
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
        try:
            raw = json.loads(self.state_path.read_text())
            allowed = ContinuousGoalRuntimeState.__dataclass_fields__
            return ContinuousGoalRuntimeState(**{k:v for k,v in raw.items() if k in allowed})
        except Exception:
            return ContinuousGoalRuntimeState()

    def cycle(self, state):
        # V29_BIG_RUNTIME_STABILIZATION
        state.cycles += 1
        cycle_errors = []
        dispatched = 0
        try:
            execution_results = self.execution_loop.run_bounded_batch(max_dispatches=self.execution_batch_size)
            dispatched = sum(1 for r in execution_results if r.dispatched)
            state.execution_dispatched += dispatched
        except Exception as exc:
            state.execution_failures += 1
            cycle_errors.append(f'execution:{type(exc).__name__}:{exc}')

        # Backpressure: drain executable backlog before adding more goal intake.
        if dispatched == 0:
            try:
                result = self.scheduler.process_next()
                if result.processed:
                    state.goals_processed += 1
                    state.last_orchestration_id = result.orchestration_id
                    state.last_reason = result.reason
                else:
                    state.idle_cycles += 1
                    state.last_reason = result.reason
            except Exception as exc:
                state.scheduler_failures += 1
                cycle_errors.append(f'scheduler:{type(exc).__name__}:{exc}')

        # CEO failures are isolated from the working execution pump.
        try:
            ceo_state = self.ceo_runtime.load()
            ceo_state = self.ceo_runtime.cycle(ceo_state)
            if not ceo_state.ready:
                state.ceo_failures += 1
                cycle_errors.append(f'ceo:{ceo_state.reason}')
        except Exception as exc:
            state.ceo_failures += 1
            cycle_errors.append(f'ceo:{type(exc).__name__}:{exc}')

        state.running = True
        state.ready = len(cycle_errors) == 0
        if dispatched:
            state.last_reason = f'execution_pump_dispatched:{dispatched}'
        elif cycle_errors:
            state.last_reason = '|'.join(cycle_errors)[:1000]
        if any(e.startswith('execution:') for e in cycle_errors):
            state.consecutive_failures += 1
        else:
            state.consecutive_failures = 0
        self.save(state)
        return state

    def run(self, max_cycles=0):
        self.stop_path.unlink(missing_ok=True)
        state = self.load()
        # V30_FRESH_RUNTIME_SESSION
        state.running = True
        state.ready = True
        state.consecutive_failures = 0
        state.last_reason = "runtime_session_started"
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

    def drain_execution_backlog(self, batch_size: int = 32):
        from companyos.runtime.execution_drain_engine import ExecutionDrainEngine
        loop = self.ceo_runtime.ceo.execution_loop
        return ExecutionDrainEngine(
            queue=loop.queue, dispatcher=loop.dispatcher, batch_size=batch_size
        ).drain_once()

    def request_stop(self):
        self.stop_path.write_text("stop\n")
