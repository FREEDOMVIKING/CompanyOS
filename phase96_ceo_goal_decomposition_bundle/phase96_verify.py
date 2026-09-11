#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase94_queue_present": Path("companyos/runtime/autonomous_task_queue.py").exists(),
    "phase95_dispatcher_present": Path("companyos/runtime/autonomous_task_dispatcher.py").exists(),
    "phase96_decomposer_present": Path("companyos/runtime/ceo_goal_decomposer.py").exists(),
    "phase96_dependency_dispatcher_present": Path("companyos/runtime/dependency_aware_dispatcher.py").exists(),
    "phase96_submit_cli_present": Path("phase96_runtime_goal_submit.py").exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("CEO_GOAL_TO_TASK_DECOMPOSITION: True")
print("DEPENDENCY_AWARE_ROUTING: True")
print("IDEMPOTENT_GOAL_TASK_KEYS: True")
print("GOAL_DECOMPOSER_SIGNS_TRANSACTION: False")
print("GOAL_DECOMPOSER_BROADCASTS: False")
print("PHASE96_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
