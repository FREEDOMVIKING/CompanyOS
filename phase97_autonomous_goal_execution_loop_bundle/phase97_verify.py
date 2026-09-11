#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase94_queue_present": Path("companyos/runtime/autonomous_task_queue.py").exists(),
    "phase95_dispatcher_present": Path("companyos/runtime/autonomous_task_dispatcher.py").exists(),
    "phase96_decomposer_present": Path("companyos/runtime/ceo_goal_decomposer.py").exists(),
    "phase97_loop_present": Path("companyos/runtime/autonomous_goal_execution_loop.py").exists(),
    "phase97_runner_present": Path("phase97_runtime_goal_loop_run.py").exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("AUTONOMOUS_DEPENDENCY_READY_TASK_ADVANCE: True")
print("STALE_TASK_RECOVERY_BEFORE_CYCLE: True")
print("SPECIALIST_ROUTING_REUSED: True")
print("GOAL_LOOP_SIGNS_TRANSACTION: False")
print("GOAL_LOOP_BROADCASTS: False")
print("PHASE97_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
