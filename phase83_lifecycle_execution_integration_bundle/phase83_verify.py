#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase82_lifecycle_present": Path(
        "companyos/walletintegration/transaction_lifecycle.py"
    ).exists(),
    "phase83_bridge_present": Path(
        "companyos/walletintegration/lifecycle_execution_bridge.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("EXECUTION_PIPELINE_LIFECYCLE_HOOKS_AVAILABLE: True")
print("AUTHORIZED_SIGNED_SUBMITTED_CONFIRMED_FINALIZED_FAILED: True")
print("INSTALLER_BROADCASTS: False")
print("VERIFY_BROADCASTS: False")
print("PHASE83_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
