#!/usr/bin/env python3
from pathlib import Path

from companyos.walletintegration.solana_signer_key_adapter import load_signer_material
from companyos.walletintegration.solana_rpc_preflight import run_rpc_preflight


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE74_RPC_PREFLIGHT: FAIL - live_financial.env not found")

    cfg = {}
    for line in p.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip("'\"")
    return p, cfg


env_path, cfg = load_env()
rpc_url = cfg.get("SOLANA_RPC_URL", "").strip()
secret = cfg.get("SOLANA_PRIVATE_KEY", "").strip()
encoding = cfg.get("SOLANA_PRIVATE_KEY_ENCODING", "auto").strip()

if not rpc_url:
    raise SystemExit("PHASE74_RPC_PREFLIGHT: FAIL - SOLANA_RPC_URL missing")
if not secret:
    raise SystemExit("PHASE74_RPC_PREFLIGHT: FAIL - SOLANA_PRIVATE_KEY missing")

material = load_signer_material(secret, encoding)
if not material.public_address:
    raise SystemExit(
        "PHASE74_RPC_PREFLIGHT: FAIL - public address unavailable from configured key"
    )

result = run_rpc_preflight(rpc_url, material.public_address)

print("ENV_FILE:", env_path)
print("RPC_REACHABLE:", result.rpc_reachable)
print("GENESIS_HASH_AVAILABLE:", result.genesis_hash_available)
print("LATEST_BLOCKHASH_AVAILABLE:", result.latest_blockhash_available)
print("WALLET_ADDRESS:", material.public_address)
print("WALLET_BALANCE_LAMPORTS:", result.wallet_balance_lamports)
print("WALLET_BALANCE_SOL:", result.wallet_balance_sol)
print("PRIVATE_KEY_PRINTED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("TRANSACTION_BROADCAST: False")

if result.error:
    print("ERROR:", result.error)

passed = (
    result.rpc_reachable
    and result.genesis_hash_available
    and result.latest_blockhash_available
    and result.wallet_balance_lamports is not None
)

print("PHASE74_RPC_PREFLIGHT:", "PASS" if passed else "FAIL")
raise SystemExit(0 if passed else 1)
