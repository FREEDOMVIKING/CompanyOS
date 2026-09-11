#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from companyos.cryptoops import CryptoAllowlist
from companyos.moneyops import (
    TreasuryGatedMultichainBridge,
    MultichainReadiness,
    FinancialKillSwitch,
    MoneyOpsStatus,
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["status","readiness","kill","unkill","authorize"])
    ap.add_argument("--chain", default="solana")
    ap.add_argument("--amount", type=float, default=0.0)
    ap.add_argument("--balance", type=float, default=0.0)
    ap.add_argument("--destination", default="")
    ap.add_argument("--source", default=None)
    ap.add_argument("--token-mint", default=None)
    ap.add_argument("--token-contract", default=None)
    ap.add_argument("--memo", default="")
    ap.add_argument("--idempotency-key", default=None)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--signing-authorized", action="store_true")
    args = ap.parse_args()

    root = Path.home() / "companyos"

    if args.action == "status":
        print(json.dumps(MoneyOpsStatus().status(), indent=2))
        return
    if args.action == "readiness":
        print(json.dumps(MultichainReadiness(root).inspect(), indent=2))
        return
    if args.action == "kill":
        print(json.dumps(FinancialKillSwitch(root).engage("manual_cli"), indent=2))
        return
    if args.action == "unkill":
        print(json.dumps(FinancialKillSwitch(root).clear(), indent=2))
        return

    bridge = TreasuryGatedMultichainBridge(
        root,
        allowlist=CryptoAllowlist(root).load()
    )
    result = bridge.authorize_and_execute(
        chain=args.chain,
        amount=args.amount,
        balance=args.balance,
        destination=args.destination,
        source=args.source,
        token_mint=args.token_mint,
        token_contract=args.token_contract,
        memo=args.memo,
        idempotency_key=args.idempotency_key,
        signing_authorized=args.signing_authorized,
        dry_run=not args.live,
    )
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
