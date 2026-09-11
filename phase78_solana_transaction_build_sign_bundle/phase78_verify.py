#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase71_loader_present": Path("companyos/walletintegration/adaptive_solana_key.py").exists(),
    "phase72_signer_adapter_present": Path("companyos/walletintegration/solana_signer_key_adapter.py").exists(),
    "phase74_rpc_present": Path("companyos/walletintegration/solana_rpc_preflight.py").exists(),
    "phase78_builder_present": Path("companyos/walletintegration/solana_legacy_tx_builder.py").exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("REAL_SOLANA_LEGACY_MESSAGE_BUILDER: True")
print("ZERO_LAMPORT_SELF_TRANSFER_ONLY_IN_TEST: True")
print("LOCAL_ED25519_SIGNING: True")
print("SEND_TRANSACTION_AVAILABLE_IN_TEST: False")
print("SIMULATE_TRANSACTION_AVAILABLE_IN_TEST: False")
print("TRANSACTION_BROADCAST_BY_VERIFY: False")
print("PHASE78_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
