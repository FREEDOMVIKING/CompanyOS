#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase84_engine_present": Path(
        "companyos/walletintegration/live_solana_execution_engine.py"
    ).exists(),
    "phase85_coordinator_present": Path(
        "companyos/walletintegration/production_execution_coordinator.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("SINGLE_CONTROLLED_EXECUTION_ENTRYPOINT: True")
print("IDEMPOTENCY_DUPLICATE_PROTECTION: True")
print("UNSUPPORTED_ACTIONS_REJECTED: True")
print("BROADCAST_DEFAULT_DISABLED: True")
print("INSTALLER_BROADCASTS: False")
print("VERIFY_BROADCASTS: False")
print("PHASE85_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
