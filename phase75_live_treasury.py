#!/usr/bin/env python3
from pathlib import Path
import time

from companyos.walletintegration.solana_signer_key_adapter import load_signer_material
from companyos.walletintegration.live_treasury_feed import LiveTreasuryFeed


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE75_LIVE_TREASURY: FAIL - live_financial.env not found")

    cfg = {}
    for line in p.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip("'\"")
    return p, cfg


env_path, cfg = load_env()
rpc_url = cfg.get("SOLANA_RPC_URL", "")
secret = cfg.get("SOLANA_PRIVATE_KEY", "")
encoding = cfg.get("SOLANA_PRIVATE_KEY_ENCODING", "auto")
reserve_sol = float(cfg.get("COMPANYOS_LIVE_MIN_RESERVE", "0") or 0)

if not rpc_url or not secret:
    raise SystemExit("PHASE75_LIVE_TREASURY: FAIL - RPC or key missing")

material = load_signer_material(secret, encoding)
if not material.public_address:
    raise SystemExit("PHASE75_LIVE_TREASURY: FAIL - public address unavailable")

feed = LiveTreasuryFeed(
    rpc_url,
    material.public_address,
    reserve_sol=reserve_sol,
    stale_after_seconds=60,
)

snap = feed.fetch()

print("ENV_FILE:", env_path)
print("WALLET_ADDRESS:", snap.wallet_address)
print("RPC_OK:", snap.rpc_ok)
print("SOL_BALANCE:", snap.sol_balance)
print("RESERVE_SOL:", snap.reserve_sol)
print("SPENDABLE_SOL:", snap.spendable_sol)
print("STALE:", snap.stale)
print("AGE_SECONDS:", round(snap.age_seconds, 3))
print("STATE_FILE:", feed.state_path)
print("PRIVATE_KEY_PRINTED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("TRANSACTION_BROADCAST: False")
print("PHASE75_LIVE_TREASURY:", "PASS" if snap.rpc_ok and not snap.stale else "FAIL")
raise SystemExit(0 if snap.rpc_ok and not snap.stale else 1)
