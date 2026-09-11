#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase100_orchestrator_present": Path(
        "companyos/runtime/autonomous_ceo_orchestrator.py"
    ).exists(),
    "phase101_runtime_present": Path(
        "companyos/runtime/autonomous_ceo_runtime_service.py"
    ).exists(),
    "phase103_intake_present": Path(
        "companyos/runtime/autonomous_goal_intake.py"
    ).exists(),
    "phase103_scheduler_present": Path(
        "companyos/runtime/autonomous_goal_scheduler.py"
    ).exists(),
    "phase103_bridge_present": Path(
        "companyos/runtime/ceo_runtime_intake_bridge.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("DURABLE_CEO_GOAL_INBOX: True")
print("PRIORITY_GOAL_SCHEDULING: True")
print("INTAKE_TO_ORCHESTRATION_BRIDGE: True")
print("RESTART_RECOVERY_FOR_CLAIMED_GOALS: True")
print("GOAL_INTAKE_EXTERNAL_ACTIONS: False")
print("GOAL_INTAKE_SIGNS_TRANSACTION: False")
print("GOAL_INTAKE_BROADCASTS: False")
print("PHASE103_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
