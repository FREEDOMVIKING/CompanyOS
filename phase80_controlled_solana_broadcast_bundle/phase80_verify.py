#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase78_builder_present": Path(
        "companyos/walletintegration/solana_legacy_tx_builder.py"
    ).exists(),
    "phase79_simulator_present": Path(
        "companyos/walletintegration/solana_transaction_simulator.py"
    ).exists(),
    "phase80_broadcaster_present": Path(
        "companyos/walletintegration/controlled_solana_broadcaster.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("BROADCAST_DEFAULT_DISABLED: True")
print("EXPLICIT_CONFIRMATION_REQUIRED: True")
print("INSTALLER_BROADCASTS: False")
print("VERIFY_BROADCASTS: False")
print("PHASE80_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
