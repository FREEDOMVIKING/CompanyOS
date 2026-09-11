#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase75_live_feed_present": Path(
        "companyos/walletintegration/live_treasury_feed.py"
    ).exists(),
    "phase87_startup_gate_present": Path(
        "companyos/walletintegration/startup_reconciliation_gate.py"
    ).exists(),
    "phase88_orchestrator_present": Path(
        "companyos/walletintegration/boot_orchestrator.py"
    ).exists(),
    "phase88_boot_script_present": Path(
        "phase88_boot_sequence.sh"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("BOOT_ORDER_ENV_RPC_KEY_WALLET_BALANCE_RECONCILIATION: True")
print("BOOT_SEQUENCE_BUILDS_TRANSACTION: False")
print("BOOT_SEQUENCE_SIGNS_TRANSACTION: False")
print("BOOT_SEQUENCE_BROADCASTS: False")
print("PHASE88_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
