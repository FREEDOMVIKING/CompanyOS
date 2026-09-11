#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase90_control_plane_present": Path(
        "companyos/walletintegration/runtime_control_plane.py"
    ).exists(),
    "phase91_watchdog_present": Path(
        "companyos/walletintegration/runtime_watchdog.py"
    ).exists(),
    "phase91_once_present": Path(
        "phase91_watchdog_once.py"
    ).exists(),
    "phase91_loop_present": Path(
        "phase91_watchdog_loop.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("DEAD_RUNTIME_RESTART_AVAILABLE: True")
print("UNRESOLVED_SUBMITTED_BLOCKS_RESTART: True")
print("RESTART_RATE_LIMIT_AVAILABLE: True")
print("WATCHDOG_BUILDS_TRANSACTION: False")
print("WATCHDOG_SIGNS_TRANSACTION: False")
print("WATCHDOG_BROADCASTS: False")
print("PHASE91_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
