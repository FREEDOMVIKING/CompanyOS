from __future__ import annotations

from dataclasses import dataclass

from companyos.runtime.autonomous_goal_scheduler import AutonomousGoalScheduler
from companyos.runtime.autonomous_ceo_runtime_service import AutonomousCEORuntimeService


@dataclass(frozen=True)
class IntakeBridgeCycle:
    intake_processed: bool
    intake_reason: str
    orchestration_id: str | None
    runtime_cycle_completed: bool
    active_orchestrations: int
    completed_orchestrations: int
    failed_orchestrations: int


class CEORuntimeIntakeBridge:
    """
    One bounded cycle:
      goal intake -> orchestration creation -> CEO runtime advancement
    """

    def __init__(self) -> None:
        self.scheduler = AutonomousGoalScheduler()
        self.runtime = AutonomousCEORuntimeService(interval_seconds=10)

    def cycle(self) -> IntakeBridgeCycle:
        sched = self.scheduler.process_next()

        state_path = self.runtime.state_path
        if state_path.exists():
            import json
            from companyos.runtime.autonomous_ceo_runtime_service import CEORuntimeServiceState
            data = json.loads(state_path.read_text(encoding="utf-8"))
            state = CEORuntimeServiceState(**data)
        else:
            state = self.runtime.startup()

        state = self.runtime.cycle(state)

        return IntakeBridgeCycle(
            intake_processed=sched.processed,
            intake_reason=sched.reason,
            orchestration_id=sched.orchestration_id,
            runtime_cycle_completed=True,
            active_orchestrations=state.active_orchestrations,
            completed_orchestrations=state.completed_orchestrations,
            failed_orchestrations=state.failed_orchestrations,
        )
