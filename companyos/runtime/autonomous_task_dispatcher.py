from __future__ import annotations
from companyos.runtime.lease_execution_guard import LeaseExecutionGuard
import time
from dataclasses import dataclass
from typing import Any,Callable,Optional
from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue,TaskRecord
@dataclass(frozen=True)
class DispatchResult:
    dispatched:bool; task_id:Optional[str]; agent_name:Optional[str]; state:Optional[str]; reason:str; result:Any
class AutonomousTaskDispatcher:
    def __init__(self,queue:AutonomousTaskQueue|None=None)->None:
        self.queue=queue or AutonomousTaskQueue(); self.handlers={}
    def register(self,*,task_type:str,agent_name:str,handler:Callable[[TaskRecord],Any])->None:
        self.handlers[task_type]=(agent_name,handler)
    def dispatch_task(self, task: TaskRecord) -> DispatchResult:
        # V39_CLEAN_FENCED_DISPATCH
        now = time.time()
        task = self.queue.load(task.task_id)

        if task.state != "QUEUED":
            return DispatchResult(False, task.task_id, None, task.state, "task_not_queued", None)
        if task.attempts >= task.max_attempts:
            return DispatchResult(False, task.task_id, None, task.state, "attempts_exhausted", None)
        if task.next_attempt_unix > now:
            return DispatchResult(False, task.task_id, None, task.state, "retry_not_due", None)
        if task.task_type not in self.handlers:
            return DispatchResult(False, task.task_id, None, task.state, "unsupported_task_type", None)

        agent, handler = self.handlers[task.task_type]
        task.state = "CLAIMED"
        task.assigned_agent = agent
        task.updated_at_unix = now
        self.queue.save(task)
        task = self.queue.mark_running(task)

        try:
            guard = LeaseExecutionGuard(self.queue.kernel.db_path)
            task_id = str(task.task_id)
            owner = "dispatcher-" + str(id(self))
            ok, result, error = guard.execute(
                task_id,
                owner,
                lambda: handler(task),
            )
            if not ok:
                raise RuntimeError(error or "leased_execution_failed")

            task = self.queue.complete(task, result)
            return DispatchResult(True, task.task_id, agent, task.state, "completed", result)
        except Exception as exc:
            task = self.queue.fail(
                task,
                f"{type(exc).__name__}:{exc}",
                retry_delay_seconds=30,
            )
            return DispatchResult(True, task.task_id, agent, task.state, "handler_failed", None)
    def dispatch_next(self)->DispatchResult:
        now=time.time()
        c=[t for t in self.queue.bounded_candidates(1024) if t.task_type in self.handlers and t.next_attempt_unix<=now]
        if not c:return DispatchResult(False,None,None,None,"no_supported_task_available",None)
        c.sort(key=lambda t:(-int(t.priority),float(t.created_at_unix),t.task_id))
        return self.dispatch_task(c[0])
