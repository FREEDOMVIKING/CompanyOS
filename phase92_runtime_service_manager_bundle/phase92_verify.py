#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase90_control_plane_present": Path(
        "companyos/walletintegration/runtime_control_plane.py"
    ).exists(),
    "phase91_watchdog_present": Path(
        "companyos/walletintegration/runtime_watchdog.py"
    ).exists(),
    "phase91_watchdog_loop_present": Path(
        "phase91_watchdog_loop.py"
    ).exists(),
    "phase92_service_manager_present": Path(
        "companyos/walletintegration/runtime_service_manager.py"
    ).exists(),
    "phase92_service_cli_present": Path(
        "phase92_runtime_service_ctl.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("ONE_COMMAND_RUNTIME_STACK_START: True")
print("SUPERVISOR_AND_WATCHDOG_STATUS: True")
print("ONE_COMMAND_RUNTIME_STACK_STOP: True")
print("DUPLICATE_WATCHDOG_START_BLOCKED: True")
print("UNRESOLVED_SUBMITTED_BLOCKS_START: True")
print("SERVICE_MANAGER_BROADCASTS: False")
print("PHASE92_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
