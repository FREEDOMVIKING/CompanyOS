#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase71_loader_present": Path(
        "companyos/walletintegration/adaptive_solana_key.py"
    ).exists(),
    "phase72_signer_adapter_present": Path(
        "companyos/walletintegration/solana_signer_key_adapter.py"
    ).exists(),
    "phase73_offline_proof_present": Path(
        "companyos/walletintegration/offline_ed25519_proof.py"
    ).exists(),
    "phase74_rpc_preflight_present": Path(
        "companyos/walletintegration/solana_rpc_preflight.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("NETWORK_READ_ONLY_CHECKS_ONLY: True")
print("TRANSACTION_CREATED_BY_VERIFY: False")
print("TRANSACTION_SIGNED_BY_VERIFY: False")
print("TRANSACTION_BROADCAST_BY_VERIFY: False")
print("PHASE74_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
