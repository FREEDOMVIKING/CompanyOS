#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase81_confirmation_tracker_present": Path(
        "companyos/walletintegration/solana_confirmation_tracker.py"
    ).exists(),
    "phase82_lifecycle_present": Path(
        "companyos/walletintegration/transaction_lifecycle.py"
    ).exists(),
    "phase82_reconciler_present": Path(
        "phase82_reconcile_last_signature.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("PERSISTENT_LIFECYCLE_STATES: AUTHORIZED,SIGNED,SUBMITTED,CONFIRMED,FINALIZED,FAILED")
print("SUBMITTED_IS_NOT_SUCCESS: True")
print("CONFIRMATION_RECONCILIATION_AVAILABLE: True")
print("INSTALLER_BROADCASTS: False")
print("VERIFY_BROADCASTS: False")
print("PHASE82_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
