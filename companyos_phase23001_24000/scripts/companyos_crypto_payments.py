#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from companyos.cryptoops import ExistingWalletAdapter, CryptoPaymentConnector, CryptoAllowlist
from companyos.paymentops import PaymentOrchestrator
from companyos.treasuryops import TreasuryPolicy

def load_binding(root):
    p = root / ".companyos_runtime" / "crypto_wallet_binding.json"
    if not p.exists():
        raise SystemExit("ERROR: run companyos_crypto_bind.py first")
    return json.loads(p.read_text(encoding="utf-8"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["status","authorize"])
    ap.add_argument("--amount", type=float, default=0.0)
    ap.add_argument("--destination", default="")
    ap.add_argument("--purpose", default="")
    args = ap.parse_args()

    root = Path.home() / "companyos"
    binding = load_binding(root)
    adapter = ExistingWalletAdapter(binding["wallet_file"])
    connector = CryptoPaymentConnector(adapter)

    if args.action == "status":
        print(json.dumps({
            "success": True,
            "wallet_file": binding["wallet_file"],
            "health": connector.health(),
            "allowlist": sorted(CryptoAllowlist(root).load()),
            "policy": TreasuryPolicy.from_env().to_dict()
        }, indent=2))
        return

    orch = PaymentOrchestrator(
        root,
        connector,
        allowlist=CryptoAllowlist(root).load(),
        policy=TreasuryPolicy.from_env()
    )
    result = orch.request_transfer(
        amount=args.amount,
        destination=args.destination,
        purpose=args.purpose
    )
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
