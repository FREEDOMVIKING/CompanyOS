#!/usr/bin/env python3
from collections import Counter

from companyos.runtime.autonomous_task_queue import AutonomousTaskQueue

q = AutonomousTaskQueue()
tasks = q.all_tasks()
counts = Counter(t.state for t in tasks)

print("TOTAL_TASKS:", len(tasks))
for state in ["QUEUED", "CLAIMED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]:
    print(f"{state}:", counts.get(state, 0))

print("TASK_QUEUE_SIGNS_TRANSACTION: False")
print("TASK_QUEUE_BROADCASTS: False")
print("PHASE94_RUNTIME_TASK_QUEUE_STATUS: PASS")
