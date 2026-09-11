#!/usr/bin/env python3
from pathlib import Path

from companyos.walletintegration.solana_signer_key_adapter import load_signer_material
from companyos.walletintegration.live_treasury_feed import LiveTreasuryFeed
from companyos.walletintegration.live_treasury_authorizer import LiveTreasuryAuthorizer
from companyos.walletintegration.execution_gate_treasury_bridge import ExecutionGateTreasuryBridge


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE77_EXECUTION_GATE_BRIDGE: FAIL - env file not found")

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
    raise SystemExit("PHASE77_EXECUTION_GATE_BRIDGE: FAIL - RPC or key missing")

material = load_signer_material(secret, enc)
if not material.public_address:
    raise SystemExit("PHASE77_EXECUTION_GATE_BRIDGE: FAIL - public address unavailable")

feed = LiveTreasuryFeed(
    rpc,
    material.public_address,
    reserve_sol=reserve,
    stale_after_seconds=60,
)

authorizer = LiveTreasuryAuthorizer(feed)
bridge = ExecutionGateTreasuryBridge(authorizer)

# Zero-value authorization test only.
result = bridge.authorize_execution(0.0, {"mode": "phase77_test"})

print("ENV_FILE:", env_path)
print("WALLET_ADDRESS:", material.public_address)
print("EXECUTION_GATE_LIVE_TREASURY_CHECK:", True)
print("REQUESTED_SOL:", result.requested_sol)
print("AUTHORIZED:", result.allowed)
print("REASON:", result.reason)
print("BALANCE_SOL:", result.balance_sol)
print("SPENDABLE_SOL:", result.spendable_sol)
print("RESERVE_SOL:", result.reserve_sol)
print("RPC_OK:", result.rpc_ok)
print("STALE:", result.stale)
print("PRIVATE_KEY_PRINTED: False")
print("TRANSACTION_CREATED: False")
print("TRANSACTION_SIGNED: False")
print("TRANSACTION_BROADCAST: False")

passed = (
    result.allowed
    and result.rpc_ok
    and not result.stale
    and result.reason == "fresh_balance_authorized"
)

print("PHASE77_EXECUTION_GATE_BRIDGE:", "PASS" if passed else "FAIL")
raise SystemExit(0 if passed else 1)
