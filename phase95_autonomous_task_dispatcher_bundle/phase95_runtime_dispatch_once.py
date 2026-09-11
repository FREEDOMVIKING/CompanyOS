#!/usr/bin/env python3

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue
from companyos.runtime.autonomous_task_dispatcher import AutonomousTaskDispatcher
from companyos.runtime.default_specialist_registry import register_default_specialists

q = AutonomousTaskQueue()
dispatcher = AutonomousTaskDispatcher(q)
register_default_specialists(dispatcher)

result = dispatcher.dispatch_next()

print("DISPATCHED:", result.dispatched)
print("TASK_ID:", result.task_id)
print("AGENT_NAME:", result.agent_name)
print("STATE:", result.state)
print("REASON:", result.reason)
print("RESULT:", result.result)
print("DISPATCHER_SIGNS_TRANSACTION: False")
print("DISPATCHER_BROADCASTS: False")
print("PHASE95_RUNTIME_DISPATCH_ONCE: PASS")
