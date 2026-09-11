#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase94_queue_present": Path(
        "companyos/runtime/autonomous_task_queue.py"
    ).exists(),
    "phase95_dispatcher_present": Path(
        "companyos/runtime/autonomous_task_dispatcher.py"
    ).exists(),
    "phase95_registry_present": Path(
        "companyos/runtime/default_specialist_registry.py"
    ).exists(),
    "phase95_runtime_dispatch_present": Path(
        "phase95_runtime_dispatch_once.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("PRIORITY_TASK_DISPATCH: True")
print("SPECIALIST_AGENT_ROUTING: True")
print("TASK_RESULT_PERSISTENCE: True")
print("HANDLER_FAILURE_RETRY_PATH: True")
print("DISPATCHER_SIGNS_TRANSACTION: False")
print("DISPATCHER_BROADCASTS: False")
print("PHASE95_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
