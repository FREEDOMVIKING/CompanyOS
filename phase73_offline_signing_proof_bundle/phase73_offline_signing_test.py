#!/usr/bin/env python3
from pathlib import Path

from companyos.walletintegration.offline_ed25519_proof import prove_ed25519_signing


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE73_OFFLINE_SIGNING_TEST: FAIL - env file not found")

    cfg = {}
    for line in p.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip("'\"")
    return p, cfg


env_path, cfg = load_env()
secret = cfg.get("SOLANA_PRIVATE_KEY", "")
encoding = cfg.get("SOLANA_PRIVATE_KEY_ENCODING", "auto")

if not secret:
    raise SystemExit("PHASE73_OFFLINE_SIGNING_TEST: FAIL - key missing")

try:
    proof = prove_ed25519_signing(secret, encoding)
except Exception as exc:
    print("OFFLINE_SIGNATURE_CREATED: False")
    print("OFFLINE_SIGNATURE_VERIFIED: False")
    print("ERROR_TYPE:", type(exc).__name__)
    print("ERROR:", str(exc)[:300])
    print("PRIVATE_KEY_PRINTED: False")
    print("TRANSACTION_CREATED: False")
    print("RPC_CALLED: False")
    print("TRANSACTION_BROADCAST: False")
    raise SystemExit(1)

print("ENV_FILE:", env_path)
print("SIGNING_BACKEND:", proof.backend)
print("OFFLINE_SIGNATURE_CREATED: True")
print("OFFLINE_SIGNATURE_VERIFIED:", proof.signature_verified)
print("PUBLIC_ADDRESS_AVAILABLE:", bool(proof.public_address))
if proof.public_address:
    print("DERIVED_SOLANA_PUBLIC_ADDRESS:", proof.public_address)
print("CHALLENGE_SHA256:", proof.message_sha256)
print("PRIVATE_KEY_PRINTED: False")
print("TRANSACTION_CREATED:", proof.transaction_created)
print("RPC_CALLED: False")
print("TRANSACTION_BROADCAST:", proof.transaction_broadcast)
print(
    "PHASE73_OFFLINE_SIGNING_TEST:",
    "PASS" if proof.signature_verified else "FAIL"
)
raise SystemExit(0 if proof.signature_verified else 1)
