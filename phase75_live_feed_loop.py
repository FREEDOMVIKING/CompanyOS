#!/usr/bin/env python3
from pathlib import Path
import argparse
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
        raise SystemExit("live_financial.env not found")

    cfg = {}
    for line in p.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip("'\"")
    return cfg


ap = argparse.ArgumentParser()
ap.add_argument("--interval", type=float, default=20.0)
args = ap.parse_args()

cfg = load_env()
material = load_signer_material(
    cfg["SOLANA_PRIVATE_KEY"],
    cfg.get("SOLANA_PRIVATE_KEY_ENCODING", "auto"),
)

feed = LiveTreasuryFeed(
    cfg["SOLANA_RPC_URL"],
    material.public_address,
    reserve_sol=float(cfg.get("COMPANYOS_LIVE_MIN_RESERVE", "0") or 0),
    stale_after_seconds=max(60.0, args.interval * 3),
)

print("COMPANYOS_LIVE_TREASURY_FEED: STARTED")
print("INTERVAL_SECONDS:", args.interval)
print("WALLET_ADDRESS:", material.public_address)
print("CTRL+C_TO_STOP: True")

while True:
    snap = feed.fetch()
    print(
        f"SOL={snap.sol_balance:.9f} "
        f"SPENDABLE={snap.spendable_sol:.9f} "
        f"RPC_OK={snap.rpc_ok} "
        f"STALE={snap.stale}"
    )
    time.sleep(max(5.0, args.interval))
