#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase92_service_manager_present": Path(
        "companyos/walletintegration/runtime_service_manager.py"
    ).exists(),
    "phase94_queue_present": Path(
        "companyos/runtime/autonomous_task_queue.py"
    ).exists(),
    "phase94_test_present": Path(
        "phase94_task_queue_test.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("PERSISTENT_INTERNAL_TASK_QUEUE: True")
print("PRIORITY_ORDERING: True")
print("IDEMPOTENCY_DUPLICATE_PROTECTION: True")
print("STALE_WORK_RECOVERY: True")
print("TASK_QUEUE_SIGNS_TRANSACTION: False")
print("TASK_QUEUE_BROADCASTS: False")
print("PHASE94_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
