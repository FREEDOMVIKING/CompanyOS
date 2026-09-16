from __future__ import annotations

# V27_9_3_BOUNDED_EXECUTION
from companyos.runtime.bounded_task_execution import run_bounded
from dataclasses import dataclass
from typing import Any
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

@dataclass(frozen=True)
class DrainResult:
    attempted: int
    dispatched: int
    stopped_reason: str
    last_result: Any = None

class ExecutionDrainEngine:
    def __init__(self, queue: AutonomousTaskQueue, dispatcher: Any, batch_size: int = 32):
        if dispatcher is None or not hasattr(dispatcher, "dispatch_next"):
            raise TypeError("live_dependency_dispatcher_required")
        self.queue=queue
        self.dispatcher=dispatcher
        self.batch_size=max(1,min(int(batch_size),64))

    def drain_once(self) -> DrainResult:
        attempted=dispatched=0
        last=None
        for _ in range(self.batch_size):
            attempted += 1
            last=self.dispatcher.dispatch_next()
            if not getattr(last,"dispatched",False):
                return DrainResult(attempted,dispatched,str(getattr(last,"reason","not_dispatched")),last)
            dispatched += 1
        return DrainResult(attempted,dispatched,"batch_limit",last)
