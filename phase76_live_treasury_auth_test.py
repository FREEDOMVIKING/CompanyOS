#!/usr/bin/env python3
from pathlib import Path

from companyos.walletintegration.solana_signer_key_adapter import load_signer_material
from companyos.walletintegration.live_treasury_feed import LiveTreasuryFeed
from companyos.walletintegration.live_treasury_authorizer import LiveTreasuryAuthorizer


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE76_LIVE_TREASURY_AUTH: FAIL - env file not found")

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

if not rpc or not secret:
    raise SystemExit("PHASE76_LIVE_TREASURY_AUTH: FAIL - RPC or key missing")

material = load_signer_material(secret, enc)
if not material.public_address:
    raise SystemExit("PHASE76_LIVE_TREASURY_AUTH: FAIL - public address unavailable")

feed = LiveTreasuryFeed(
    rpc,
    material.public_address,
    reserve_sol=reserve,
    stale_after_seconds=60,
)

auth = LiveTreasuryAuthorizer(feed)

# Test only with zero SOL request.
# This exercises forced-fresh authorization without creating/signing/broadcasting tx.
decision = auth.authorize_sol(0.0)

print("ENV_FILE:", env_path)
print("WALLET_ADDRESS:", material.public_address)
print("REQUESTED_SOL:", decision.requested_sol)
print("AUTH_ALLOWED:", decision.allowed)
print("AUTH_REASON:", decision.reason)
print("CURRENT_BALANCE_SOL:", decision.current_balance_sol)
print("RESERVE_SOL:", decision.reserve_sol)
print("SPENDABLE_SOL:", decision.spendable_sol)
print("RPC_OK:", decision.rpc_ok)
print("STALE:", decision.stale)
print("FORCED_FRESH_BALANCE_USED: True")
print("PRIVATE_KEY_PRINTED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("TRANSACTION_BROADCAST: False")

passed = (
    decision.allowed
    and decision.rpc_ok
    and not decision.stale
    and decision.reason == "fresh_balance_authorized"
)

print("PHASE76_LIVE_TREASURY_AUTH:", "PASS" if passed else "FAIL")
raise SystemExit(0 if passed else 1)
