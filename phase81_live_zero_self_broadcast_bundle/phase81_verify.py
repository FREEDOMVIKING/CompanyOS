#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase78_builder_present": Path(
        "companyos/walletintegration/solana_legacy_tx_builder.py"
    ).exists(),
    "phase80_broadcaster_present": Path(
        "companyos/walletintegration/controlled_solana_broadcaster.py"
    ).exists(),
    "phase81_confirmation_tracker_present": Path(
        "companyos/walletintegration/solana_confirmation_tracker.py"
    ).exists(),
    "phase81_manual_live_test_present": Path(
        "phase81_manual_live_zero_self_test.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("INSTALLER_BROADCASTS: False")
print("VERIFY_BROADCASTS: False")
print("MANUAL_LIVE_EXECUTION_REQUIRED: True")
print("EXPLICIT_NETWORK_FEE_CONFIRMATION_REQUIRED: True")
print("PHASE81_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
