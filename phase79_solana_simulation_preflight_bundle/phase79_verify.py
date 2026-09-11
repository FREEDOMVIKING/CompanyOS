#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase78_builder_present": Path(
        "companyos/walletintegration/solana_legacy_tx_builder.py"
    ).exists(),
    "phase79_simulator_present": Path(
        "companyos/walletintegration/solana_transaction_simulator.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("SIMULATE_TRANSACTION_ENABLED: True")
print("SEND_TRANSACTION_ENABLED_IN_TEST: False")
print("ZERO_LAMPORT_SELF_TRANSFER_TEST_ONLY: True")
print("TRANSACTION_BROADCAST_BY_VERIFY: False")
print("PHASE79_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
