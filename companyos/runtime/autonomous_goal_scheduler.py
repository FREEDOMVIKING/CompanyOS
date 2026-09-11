from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from companyos.runtime.autonomous_goal_intake import AutonomousGoalIntake
from companyos.runtime.autonomous_ceo_orchestrator import AutonomousCEOOrchestrator


@dataclass(frozen=True)
class GoalSchedulerResult:
    processed: bool
    intake_id: Optional[str]
    orchestration_id: Optional[str]
    reason: str


class AutonomousGoalScheduler:
    """
    Converts durable intake records into Phase 100 CEO orchestrations.

    Each call processes at most one goal.
    """

    def __init__(
        self,
        *,
        intake: AutonomousGoalIntake | None = None,
        ceo: AutonomousCEOOrchestrator | None = None,
    ) -> None:
        self.intake = intake or AutonomousGoalIntake()
        self.ceo = ceo or AutonomousCEOOrchestrator()

    def process_next(self) -> GoalSchedulerResult:
        self.intake.recover_claimed()
        record = self.intake.claim_next()

        if record is None:
            return GoalSchedulerResult(
                False, None, None, "goal_intake_empty"
            )

        try:
            orchestration_id = f"intake-{record.intake_id}"

            self.ceo.start(
                goal=record.goal,
                orchestration_id=orchestration_id,
                max_cycles=100,
                max_follow_up_depth=2,
                priority_base=record.priority,
            )

            self.intake.mark_submitted(
                record,
                orchestration_id=orchestration_id,
            )

            return GoalSchedulerResult(
                True,
                record.intake_id,
                orchestration_id,
                "orchestration_created",
            )

        except Exception as exc:
            self.intake.fail(
                record,
                f"{type(exc).__name__}:{str(exc)}",
            )
            return GoalSchedulerResult(
                True,
                record.intake_id,
                None,
                "orchestration_create_failed",
            )
