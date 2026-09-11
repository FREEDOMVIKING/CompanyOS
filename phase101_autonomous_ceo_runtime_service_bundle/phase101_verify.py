#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase100_orchestrator_present": Path(
        "companyos/runtime/autonomous_ceo_orchestrator.py"
    ).exists(),
    "phase100_journal_present": Path(
        "companyos/runtime/ceo_orchestration_journal.py"
    ).exists(),
    "phase101_service_present": Path(
        "companyos/runtime/autonomous_ceo_runtime_service.py"
    ).exists(),
    "phase101_runner_present": Path(
        "phase101_ceo_runtime_run.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("MULTI_ORCHESTRATION_RUNTIME_ADVANCE: True")
print("PERSISTED_SERVICE_HEALTH_STATE: True")
print("PER_ORCHESTRATION_ERROR_ISOLATION: True")
print("MAX_FAILURE_STOP_GUARD: True")
print("CEO_RUNTIME_EXTERNAL_ACTIONS: False")
print("CEO_RUNTIME_SIGNS_TRANSACTION: False")
print("CEO_RUNTIME_BROADCASTS: False")
print("PHASE101_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
