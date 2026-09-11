#!/usr/bin/env python3
"""
MANUAL LIVE TEST.

Broadcasts ONE zero-lamport self-transfer on Solana.

This is a real on-chain transaction and can consume a real network fee.
It intentionally transfers 0 lamports to the same wallet.
"""

import argparse
import time
from pathlib import Path

from companyos.walletintegration.solana_rpc_preflight import rpc_call
from companyos.walletintegration.solana_legacy_tx_builder import build_zero_lamport_self_transfer
from companyos.walletintegration.controlled_solana_broadcaster import ControlledSolanaBroadcaster
from companyos.walletintegration.solana_confirmation_tracker import wait_for_signature_status


CONFIRM_TEXT = "I_ACCEPT_ONE_REAL_SOLANA_NETWORK_FEE"


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("live_financial.env not found")

    cfg = {}
    for line in p.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip("'\"")
    return p, cfg


def get_balance(rpc, address):
    data = rpc_call(rpc, "getBalance", [address, {"commitment": "confirmed"}])
    return int((data.get("result") or {}).get("value"))


ap = argparse.ArgumentParser()
ap.add_argument("--execute-live", action="store_true")
ap.add_argument("--confirm", default="")
args = ap.parse_args()

if not args.execute_live:
    raise SystemExit("LIVE_BROADCAST_BLOCKED: --execute-live required")

if args.confirm != CONFIRM_TEXT:
    raise SystemExit(
        "LIVE_BROADCAST_BLOCKED: exact confirmation text required: "
        + CONFIRM_TEXT
    )

env_path, cfg = load_env()
rpc = cfg.get("SOLANA_RPC_URL", "")
secret = cfg.get("SOLANA_PRIVATE_KEY", "")
enc = cfg.get("SOLANA_PRIVATE_KEY_ENCODING", "auto")

if not rpc or not secret:
    raise SystemExit("LIVE_BROADCAST_BLOCKED: RPC or key missing")

latest = rpc_call(rpc, "getLatestBlockhash", [{"commitment": "confirmed"}])
blockhash = ((latest.get("result") or {}).get("value") or {}).get("blockhash")
if not blockhash:
    raise SystemExit("LIVE_BROADCAST_BLOCKED: latest blockhash unavailable")

tx = build_zero_lamport_self_transfer(secret, enc, blockhash)

balance_before = get_balance(rpc, tx.wallet_address)

broadcaster = ControlledSolanaBroadcaster(rpc, broadcast_enabled=True)
result = broadcaster.send_serialized_transaction(
    tx.transaction_base64,
    confirm_token=ControlledSolanaBroadcaster.REQUIRED_CONFIRM_TOKEN,
    skip_preflight=False,
    preflight_commitment="confirmed",
    max_retries=3,
)

print("ENV_FILE:", env_path)
print("LIVE_TEST:", True)
print("ZERO_LAMPORT_SELF_TRANSFER:", True)
print("NETWORK_FEE_EXPECTED:", True)
print("WALLET_ADDRESS:", tx.wallet_address)
print("BALANCE_BEFORE_LAMPORTS:", balance_before)
print("TRANSACTION_SIGNED:", tx.signature_verified)
print("SUBMITTED:", result.submitted)
print("RPC_OK:", result.rpc_ok)
print("ERROR:", result.error)
print("SIGNATURE:", result.signature)
print("PRIVATE_KEY_PRINTED: False")

if not result.submitted or not result.signature:
    print("PHASE81_LIVE_ZERO_SELF_TEST: FAIL")
    raise SystemExit(1)

confirmation = wait_for_signature_status(
    rpc,
    result.signature,
    timeout_seconds=60.0,
    poll_interval_seconds=2.0,
)

# Give RPC balance a brief moment to reflect the landed fee.
time.sleep(2.0)
balance_after = get_balance(rpc, tx.wallet_address)

fee_delta = max(0, balance_before - balance_after)

print("STATUS_FOUND:", confirmation.found)
print("CONFIRMED:", confirmation.confirmed)
print("FINALIZED:", confirmation.finalized)
print("CONFIRMATION_STATUS:", confirmation.confirmation_status)
print("STATUS_ERR:", confirmation.err)
print("SLOT:", confirmation.slot)
print("STATUS_POLLS:", confirmation.polls)
print("BALANCE_AFTER_LAMPORTS:", balance_after)
print("BALANCE_DELTA_LAMPORTS:", balance_before - balance_after)
print("OBSERVED_FEE_OR_BALANCE_DELTA_LAMPORTS:", fee_delta)
print("VALUE_TRANSFER_LAMPORTS:", 0)
print("PRIVATE_KEY_PRINTED: False")

passed = (
    result.submitted
    and confirmation.confirmed
    and confirmation.err is None
    and tx.lamports == 0
    and tx.destination == tx.wallet_address
)

print("PHASE81_LIVE_ZERO_SELF_TEST:", "PASS" if passed else "FAIL")
raise SystemExit(0 if passed else 1)
