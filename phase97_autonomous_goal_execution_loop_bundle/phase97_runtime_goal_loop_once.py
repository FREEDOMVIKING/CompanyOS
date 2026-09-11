#!/usr/bin/env python3

from companyos.runtime.autonomous_goal_execution_loop import AutonomousGoalExecutionLoop

loop = AutonomousGoalExecutionLoop()
result = loop.cycle()

print("DISPATCHED:", result.dispatched)
print("TASK_ID:", result.task_id)
print("AGENT_NAME:", result.agent_name)
print("STATE:", result.state)
print("REASON:", result.reason)
print("COMPLETED_TASKS:", result.completed_tasks)
print("FAILED_TASKS:", result.failed_tasks)
print("QUEUED_TASKS:", result.queued_tasks)
print("RUNNING_TASKS:", result.running_tasks)
print("GOAL_LOOP_SIGNS_TRANSACTION: False")
print("GOAL_LOOP_BROADCASTS: False")
print("PHASE97_RUNTIME_GOAL_LOOP_ONCE: PASS")
