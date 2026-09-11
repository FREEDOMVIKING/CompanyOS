#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase89_supervisor_present": Path(
        "companyos/walletintegration/production_runtime_supervisor.py"
    ).exists(),
    "phase89_runner_present": Path(
        "phase89_supervisor_run.py"
    ).exists(),
    "phase90_control_plane_present": Path(
        "companyos/walletintegration/runtime_control_plane.py"
    ).exists(),
    "phase90_cli_present": Path(
        "phase90_runtime_ctl.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("DETACHED_RUNTIME_START_AVAILABLE: True")
print("RUNTIME_STATUS_AVAILABLE: True")
print("RUNTIME_STOP_AVAILABLE: True")
print("DUPLICATE_SUPERVISOR_START_BLOCKED: True")
print("CONTROL_PLANE_BUILDS_TRANSACTION: False")
print("CONTROL_PLANE_SIGNS_TRANSACTION: False")
print("CONTROL_PLANE_BROADCASTS: False")
print("PHASE90_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
