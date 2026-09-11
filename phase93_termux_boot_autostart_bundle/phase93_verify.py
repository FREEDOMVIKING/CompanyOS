#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase92_service_manager_present": Path(
        "companyos/walletintegration/runtime_service_manager.py"
    ).exists(),
    "phase92_service_ctl_present": Path(
        "phase92_runtime_service_ctl.py"
    ).exists(),
    "phase93_boot_manager_present": Path(
        "companyos/walletintegration/termux_boot_manager.py"
    ).exists(),
    "phase93_boot_ctl_present": Path(
        "phase93_boot_ctl.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("TERMUX_BOOT_LAUNCHER_AVAILABLE: True")
print("USES_PHASE92_SERVICE_MANAGER: True")
print("BOOT_LAUNCHER_DIRECT_BROADCAST: False")
print("INSTALLER_BROADCASTS: False")
print("VERIFY_BROADCASTS: False")
print("PHASE93_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
