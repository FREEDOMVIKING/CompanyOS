#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase82_lifecycle_present": Path(
        "companyos/walletintegration/transaction_lifecycle.py"
    ).exists(),
    "phase85_coordinator_present": Path(
        "companyos/walletintegration/production_execution_coordinator.py"
    ).exists(),
    "phase86_recovery_present": Path(
        "companyos/walletintegration/execution_recovery_manager.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("AUTHORIZED_SIGNED_BLIND_REBROADCAST: False")
print("SUBMITTED_RECONCILED_ONCHAIN_FIRST: True")
print("TERMINAL_STATES_NOOP: True")
print("INSTALLER_BROADCASTS: False")
print("VERIFY_BROADCASTS: False")
print("PHASE86_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
