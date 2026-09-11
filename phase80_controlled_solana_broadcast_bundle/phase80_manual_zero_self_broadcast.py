#!/usr/bin/env python3
"""
MANUAL ONLY.

Broadcasts a zero-lamport self-transfer after:
1) fresh blockhash fetch
2) local transaction construction/signing
3) explicit CLI flag
4) exact confirmation token

NOTE: Even a zero-lamport transfer can still consume a Solana network fee.
"""

import argparse
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
        raise SystemExit("env file not found")

    cfg = {}
    for line in p.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip("'\"")
    return cfg


ap = argparse.ArgumentParser()
ap.add_argument("--enable-broadcast", action="store_true")
ap.add_argument("--confirm", default="")
args = ap.parse_args()

if not args.enable_broadcast:
    raise SystemExit("BROADCAST_BLOCKED: --enable-broadcast required")

if args.confirm != ControlledSolanaBroadcaster.REQUIRED_CONFIRM_TOKEN:
    raise SystemExit(
        "BROADCAST_BLOCKED: exact --confirm BROADCAST_ZERO_SELF_TRANSFER required"
    )

cfg = load_env()
rpc = cfg["SOLANA_RPC_URL"]
secret = cfg["SOLANA_PRIVATE_KEY"]
enc = cfg.get("SOLANA_PRIVATE_KEY_ENCODING", "auto")

latest = rpc_call(rpc, "getLatestBlockhash", [{"commitment": "confirmed"}])
blockhash = ((latest.get("result") or {}).get("value") or {}).get("blockhash")
if not blockhash:
    raise SystemExit("blockhash unavailable")

tx = build_zero_lamport_self_transfer(secret, enc, blockhash)

broadcaster = ControlledSolanaBroadcaster(rpc, broadcast_enabled=True)
result = broadcaster.send_serialized_transaction(
    tx.transaction_base64,
    confirm_token=args.confirm,
    skip_preflight=False,
)

print("ZERO_LAMPORT_SELF_TRANSFER:", True)
print("NETWORK_FEE_MAY_APPLY:", True)
print("SUBMITTED:", result.submitted)
print("SIGNATURE:", result.signature)
print("RPC_OK:", result.rpc_ok)
print("ERROR:", result.error)
print("PRIVATE_KEY_PRINTED: False")

raise SystemExit(0 if result.submitted else 1)
