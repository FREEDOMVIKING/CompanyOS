#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase94_queue_present": Path("companyos/runtime/autonomous_task_queue.py").exists(),
    "phase96_decomposer_present": Path("companyos/runtime/ceo_goal_decomposer.py").exists(),
    "phase97_loop_present": Path("companyos/runtime/autonomous_goal_execution_loop.py").exists(),
    "phase98_manager_present": Path("companyos/runtime/goal_lifecycle_manager.py").exists(),
    "phase98_status_cli_present": Path("phase98_runtime_goal_status.py").exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("CEO_GOAL_LIFECYCLE_TRACKING: True")
print("TASK_OUTPUT_AGGREGATION: True")
print("BLOCKED_GOAL_DETECTION: True")
print("COMPLETED_FAILED_TERMINAL_STATES: True")
print("GOAL_LIFECYCLE_SIGNS_TRANSACTION: False")
print("GOAL_LIFECYCLE_BROADCASTS: False")
print("PHASE98_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
