from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.default_specialist_registry import register_default_specialists
from companyos.runtime.dependency_aware_dispatcher import DependencyAwareDispatcher


@dataclass(frozen=True)
class GoalLoopCycleResult:
    dispatched: bool
    task_id: Optional[str]
    agent_name: Optional[str]
    state: Optional[str]
    reason: str
    completed_tasks: int
    failed_tasks: int
    queued_tasks: int
    running_tasks: int


class AutonomousGoalExecutionLoop:
    """
    Continuously advances dependency-ready internal goal tasks.

    Responsibilities:
    - recover stale Phase 94 tasks before each cycle
    - use Phase 95 specialist routing
    - obey Phase 96 dependency ordering
    - advance one eligible task per cycle
    - persist all task states/results
    - never build/sign/broadcast financial transactions itself
    """

    def __init__(self, queue: AutonomousTaskQueue | None = None) -> None:
        self.queue = queue or AutonomousTaskQueue()
        base_dispatcher = AutonomousTaskDispatcher(self.queue)
        register_default_specialists(base_dispatcher)
        required = {"research", "planning", "build"}
        missing = sorted(required.difference(base_dispatcher.handlers))
        if missing:
            raise RuntimeError("missing_default_specialist_handlers:" + ",".join(missing))
        self.dispatcher = DependencyAwareDispatcher(base_dispatcher)

    def _counts(self):
        completed = failed = queued = running = 0
        for task in self.queue.all_tasks():
            if task.state == "COMPLETED":
                completed += 1
            elif task.state == "FAILED":
                failed += 1
            elif task.state == "QUEUED":
                queued += 1
            elif task.state in ("CLAIMED", "RUNNING"):
                running += 1
        return completed, failed, queued, running

    def cycle(self) -> GoalLoopCycleResult:
        self.queue.recover_stale(stale_after_seconds=300)

        result = self.dispatcher.dispatch_next()
        completed, failed, queued, running = self._counts()

        return GoalLoopCycleResult(
            dispatched=result.dispatched,
            task_id=result.task_id,
            agent_name=result.agent_name,
            state=result.state,
            reason=result.reason,
            completed_tasks=completed,
            failed_tasks=failed,
            queued_tasks=queued,
            running_tasks=running,
        )

    def run_bounded_batch(self, *, max_dispatches: int = 8):
        # Bounded internal throughput; existing queue/dependency gates remain authoritative.
        results = []
        for _ in range(max(1, min(int(max_dispatches), 64))):
            result = self.cycle()
            results.append(result)
            if not result.dispatched:
                break
        return results

    def run_until_idle(
        self,
        *,
        max_cycles: int = 100,
        sleep_seconds: float = 0.0,
    ) -> list[GoalLoopCycleResult]:
        results = []

        for _ in range(max(1, int(max_cycles))):
            cycle = self.cycle()
            results.append(cycle)

            if cycle.reason in ("no_dependency_ready_task", "queue_empty"):
                break

            if sleep_seconds > 0:
                time.sleep(float(sleep_seconds))

        return results
