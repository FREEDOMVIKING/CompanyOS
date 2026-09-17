from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue, TaskRecord
from companyos.runtime.bounded_task_execution import run_bounded


@dataclass(frozen=True)
class DispatchResult:
    dispatched: bool
    task_id: Optional[str]
    agent_name: Optional[str]
    state: Optional[str]
    reason: str
    result: Any


class AutonomousTaskDispatcher:
    """
    Routes queued internal tasks to registered specialist handlers.

    Responsibilities:
    - claim highest-priority eligible task
    - select specialist agent by task_type
    - mark task RUNNING
    - execute handler
    - persist COMPLETED/FAILED state
    - retry according to queue policy

    This dispatcher does NOT sign or broadcast transactions.
    """

    def __init__(self, queue: AutonomousTaskQueue | None = None) -> None:
        self.queue = queue or AutonomousTaskQueue()
        self.handlers: dict[str, tuple[str, Callable[[TaskRecord], Any]]] = {}

    def register(
        self,
        *,
        task_type: str,
        agent_name: str,
        handler: Callable[[TaskRecord], Any],
    ) -> None:
        self.handlers[task_type] = (agent_name, handler)

    def dispatch_next(self) -> DispatchResult:
        # First peek at eligible tasks so unsupported task types are not
        # accidentally claimed by a generic agent.
        candidates = [
            t for t in self.queue.all_tasks()
            if t.state == "QUEUED"
            and t.attempts < t.max_attempts
        ]

        if not candidates:
            return DispatchResult(False, None, None, None, "queue_empty", None)

        supported = [t for t in candidates if t.task_type in self.handlers]
        if not supported:
            return DispatchResult(
                False, None, None, None, "no_supported_task_available", None
            )

        supported.sort(key=lambda t: (t.priority, t.created_at_unix))
        chosen = supported[0]
        agent_name, handler = self.handlers[chosen.task_type]

        # claim_next may choose a different task if unsupported tasks have
        # higher priority, so claim manually and persist atomically enough for
        # this local single-process dispatcher.
        task = self.queue.load(chosen.task_id)
        task.state = "CLAIMED"
        task.assigned_agent = agent_name
        self.queue.save(task)

        self.queue.mark_running(task)

        try:
            # V27_9_4A_LIVE_HANDLER_TIMEOUT
            _bounded = run_bounded(lambda: handler(task))
            if not _bounded.ok:
                if _bounded.timed_out:
                    raise TimeoutError(_bounded.error or 'task_timeout')
                raise RuntimeError(_bounded.error or 'task_handler_failed')
            result = _bounded.value
            self.queue.complete(task, result)
            return DispatchResult(
                True,
                task.task_id,
                agent_name,
                task.state,
                "completed",
                result,
            )
        except Exception as exc:
            self.queue.fail(
                task,
                f"{type(exc).__name__}:{str(exc)}",
                retry_delay_seconds=0,
            )
            return DispatchResult(
                True,
                task.task_id,
                agent_name,
                task.state,
                "handler_failed",
                None,
            )
