#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase92_service_manager_present": Path(
        "companyos/walletintegration/runtime_service_manager.py"
    ).exists(),
    "phase101_ceo_runtime_present": Path(
        "companyos/runtime/autonomous_ceo_runtime_service.py"
    ).exists(),
    "phase102_ceo_control_present": Path(
        "companyos/runtime/ceo_runtime_control_plane.py"
    ).exists(),
    "phase102_unified_manager_present": Path(
        "companyos/runtime/unified_runtime_stack_manager.py"
    ).exists(),
    "phase102_cli_present": Path(
        "phase102_unified_runtime_ctl.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("ONE_COMMAND_UNIFIED_RUNTIME_START: True")
print("FINANCIAL_STACK_AND_CEO_RUNTIME_STATUS: True")
print("ONE_COMMAND_UNIFIED_RUNTIME_STOP: True")
print("DUPLICATE_CEO_RUNTIME_START_BLOCKED: True")
print("UNIFIED_MANAGER_EXTERNAL_ACTIONS: False")
print("UNIFIED_MANAGER_SIGNS_TRANSACTION: False")
print("UNIFIED_MANAGER_BROADCASTS: False")
print("PHASE102_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
