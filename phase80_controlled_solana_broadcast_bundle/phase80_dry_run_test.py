#!/usr/bin/env python3
from pathlib import Path

from companyos.walletintegration.solana_rpc_preflight import rpc_call
from companyos.walletintegration.solana_legacy_tx_builder import build_zero_lamport_self_transfer
from companyos.walletintegration.controlled_solana_broadcaster import ControlledSolanaBroadcaster


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE80_DRY_RUN_TEST: FAIL - env file not found")

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
    raise SystemExit("PHASE80_DRY_RUN_TEST: FAIL - RPC or key missing")

latest = rpc_call(rpc, "getLatestBlockhash", [{"commitment": "confirmed"}])
blockhash = ((latest.get("result") or {}).get("value") or {}).get("blockhash")
if not blockhash:
    raise SystemExit("PHASE80_DRY_RUN_TEST: FAIL - blockhash unavailable")

tx = build_zero_lamport_self_transfer(secret, enc, blockhash)

# Critical: dry-run test keeps broadcaster disabled.
broadcaster = ControlledSolanaBroadcaster(rpc, broadcast_enabled=False)
result = broadcaster.send_serialized_transaction(
    tx.transaction_base64,
    confirm_token="BROADCAST_ZERO_SELF_TRANSFER",
)

print("ENV_FILE:", env_path)
print("WALLET_ADDRESS:", tx.wallet_address)
print("LAMPORTS:", tx.lamports)
print("TRANSACTION_SIGNED:", tx.signature_verified)
print("BROADCAST_ENABLED:", broadcaster.broadcast_enabled)
print("SEND_TRANSACTION_CALLED:", result.submitted)
print("EXPECTED_BLOCK_REASON:", result.error)
print("RPC_OK:", result.rpc_ok)
print("PRIVATE_KEY_PRINTED: False")
print("TRANSACTION_BROADCAST: False")
print("FUNDS_MOVED: False")

passed = (
    tx.signature_verified
    and tx.lamports == 0
    and result.submitted is False
    and result.error == "broadcast_disabled"
)

print("PHASE80_DRY_RUN_TEST:", "PASS" if passed else "FAIL")
raise SystemExit(0 if passed else 1)
