#!/usr/bin/env python3
from pathlib import Path

from companyos.walletintegration.solana_signer_key_adapter import load_signer_material
from companyos.walletintegration.live_solana_execution_engine import LiveSolanaExecutionEngine


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE84_DRY_RUN: FAIL - env file not found")

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
reserve = float(cfg.get("COMPANYOS_LIVE_MIN_RESERVE", "0") or 0)

material = load_signer_material(secret, enc)

engine = LiveSolanaExecutionEngine(
    rpc_url=rpc,
    secret=secret,
    encoding=enc,
    wallet_address=material.public_address,
    reserve_sol=reserve,
    broadcast_enabled=False,
)

result = engine.execute_zero_self_transfer(
    allow_broadcast=False,
)

print("ENV_FILE:", env_path)
print("LIFECYCLE_ID:", result.lifecycle_id)
print("STATE:", result.state)
print("SUCCESS:", result.success)
print("REASON:", result.reason)
print("BALANCE_BEFORE_LAMPORTS:", result.balance_before_lamports)
print("TRANSACTION_SIGNED_PATH_REACHED:", result.state == "SIGNED")
print("BROADCAST_REQUESTED: False")
print("TRANSACTION_BROADCAST: False")
print("PRIVATE_KEY_PRINTED: False")

passed = (
    result.success
    and result.state == "SIGNED"
    and result.reason == "signed_not_broadcast"
    and result.signature is None
)

print("PHASE84_DRY_RUN:", "PASS" if passed else "FAIL")
raise SystemExit(0 if passed else 1)
