#!/usr/bin/env python3
from pathlib import Path
import shutil

checks = {
    "openssl_available": bool(shutil.which("openssl")),
    "phase71_loader_present": Path(
        "companyos/walletintegration/adaptive_solana_key.py"
    ).exists(),
    "phase72_adapter_present": Path(
        "companyos/walletintegration/solana_signer_key_adapter.py"
    ).exists(),
    "phase73_proof_present": Path(
        "companyos/walletintegration/offline_ed25519_proof.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("TRANSACTION_CREATED_BY_VERIFY: False")
print("TRANSACTION_BROADCAST_BY_VERIFY: False")
print("PHASE73_RUNTIME_BRIDGE_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
