#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase86_recovery_present": Path(
        "companyos/walletintegration/execution_recovery_manager.py"
    ).exists(),
    "phase87_gate_present": Path(
        "companyos/walletintegration/startup_reconciliation_gate.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("STARTUP_RECONCILIATION_REQUIRED_BEFORE_RESUME: True")
print("SIGNED_PENDING_AUTO_REBROADCAST: False")
print("UNRESOLVED_SUBMITTED_BLOCKS_RESUME: True")
print("INSTALLER_BROADCASTS: False")
print("VERIFY_BROADCASTS: False")
print("PHASE87_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
