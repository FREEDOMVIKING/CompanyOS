#!/usr/bin/env python3
from pathlib import Path

from companyos.walletintegration.solana_signer_key_adapter import load_signer_material
from companyos.walletintegration.solana_rpc_preflight import rpc_call
from companyos.walletintegration.solana_legacy_tx_builder import build_zero_lamport_self_transfer


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE78_TRANSACTION_SIGN_TEST: FAIL - env file not found")

    cfg = {}
    for line in p.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip("'\"")
    return p, cfg


env_path, cfg = load_env()
rpc = cfg.get("SOLANA_RPC_URL", "")
secret = cfg.get("SOLANA_PRIVATE_KEY", "")
enc = cfg.get("SOLANA_PRIVATE_KEY_ENCODING", "auto")

if not rpc or not secret:
    raise SystemExit("PHASE78_TRANSACTION_SIGN_TEST: FAIL - RPC or key missing")

material = load_signer_material(secret, enc)
if not material.public_address:
    raise SystemExit("PHASE78_TRANSACTION_SIGN_TEST: FAIL - public address unavailable")

latest = rpc_call(rpc, "getLatestBlockhash", [{"commitment": "confirmed"}])
blockhash = ((latest.get("result") or {}).get("value") or {}).get("blockhash")
if not blockhash:
    raise SystemExit("PHASE78_TRANSACTION_SIGN_TEST: FAIL - latest blockhash unavailable")

tx = build_zero_lamport_self_transfer(secret, enc, blockhash)

print("ENV_FILE:", env_path)
print("WALLET_ADDRESS:", tx.wallet_address)
print("DESTINATION:", tx.destination)
print("LAMPORTS:", tx.lamports)
print("LATEST_BLOCKHASH_FETCHED: True")
print("TRANSACTION_MESSAGE_CREATED: True")
print("TRANSACTION_SIGNED: True")
print("SIGNATURE_LENGTH:", len(tx.signature_bytes))
print("SIGNATURE_VERIFIED_LOCALLY:", tx.signature_verified)
print("SERIALIZED_TRANSACTION_CREATED: True")
print("SERIALIZED_TRANSACTION_BYTES:", len(tx.transaction_bytes))
print("MESSAGE_SHA256:", tx.message_sha256)
print("TRANSACTION_SHA256:", tx.transaction_sha256)
print("PRIVATE_KEY_PRINTED: False")
print("SEND_TRANSACTION_CALLED: False")
print("SIMULATE_TRANSACTION_CALLED: False")
print("TRANSACTION_BROADCAST: False")
print("FUNDS_MOVED: False")

passed = (
    tx.signature_verified
    and tx.lamports == 0
    and tx.destination == tx.wallet_address
    and len(tx.signature_bytes) == 64
    and len(tx.transaction_bytes) > 64
)

print("PHASE78_TRANSACTION_SIGN_TEST:", "PASS" if passed else "FAIL")
raise SystemExit(0 if passed else 1)
