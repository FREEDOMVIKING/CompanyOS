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
    Continuous dependency-ready execution loop.

    V28.3 performs stale recovery once per batch, dependency indexing once per
    batch, and queue counting once per batch instead of once per task.
    """

    def __init__(self, queue: AutonomousTaskQueue | None = None) -> None:
        self.queue = queue or AutonomousTaskQueue()
        base_dispatcher = AutonomousTaskDispatcher(self.queue)
        register_default_specialists(base_dispatcher)
        required = {"research", "planning", "build"}
        missing = sorted(required.difference(base_dispatcher.handlers))
        if missing:
            raise RuntimeError(
                "missing_default_specialist_handlers:" + ",".join(missing)
            )
        self.dispatcher = DependencyAwareDispatcher(base_dispatcher)

    def _counts(self):
        completed = failed = queued = running = 0
        for task in self.queue._iter_task_files():
            if task.state == "COMPLETED":
                completed += 1
            elif task.state == "FAILED":
                failed += 1
            elif task.state == "QUEUED":
                queued += 1
            elif task.state in ("CLAIMED", "RUNNING"):
                running += 1
        return completed, failed, queued, running

    @staticmethod
    def _to_cycle(result, counts):
        completed, failed, queued, running = counts
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

    def cycle(self) -> GoalLoopCycleResult:
        return self.run_bounded_batch(max_dispatches=1)[0]

    def run_bounded_batch(self, *, max_dispatches: int = 8):
        # One stale scan per batch, not once per task.
        self.queue.recover_stale(stale_after_seconds=300)

        raw = self.dispatcher.dispatch_batch(max_dispatches=max_dispatches)

        # One count scan per batch, not once per task.
        counts = self._counts()
        return [self._to_cycle(result, counts) for result in raw]

    def run_until_idle(
        self,
        *,
        max_cycles: int = 100,
        sleep_seconds: float = 0.0,
    ) -> list[GoalLoopCycleResult]:
        results = []
        for _ in range(max(1, int(max_cycles))):
            batch = self.run_bounded_batch(max_dispatches=8)
            results.extend(batch)
            if not any(item.dispatched for item in batch):
                break
            if sleep_seconds > 0:
                time.sleep(float(sleep_seconds))
        return results
