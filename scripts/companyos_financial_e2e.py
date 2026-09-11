#!/usr/bin/env python3
import argparse, json
from pathlib import Path

from companyos.cryptoops import CryptoAllowlist
from companyos.finops import FinancialIntent, FinancialSimulationEngine, FinancialSafetyValidator, LiveActivationGate
from companyos.moneyops import MultichainReadiness

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chain", default="solana")
    ap.add_argument("--amount", type=float, default=1.0)
    ap.add_argument("--balance", type=float, default=1000.0)
    ap.add_argument("--destination", required=True)
    ap.add_argument("--purpose", default="CompanyOS end-to-end financial safety validation")
    ap.add_argument("--source", default=None)
    ap.add_argument("--token-mint", default=None)
    ap.add_argument("--token-contract", default=None)
    args = ap.parse_args()

    root = Path.home() / "companyos"

    intent = FinancialIntent(
        chain=args.chain,
        amount=args.amount,
        destination=args.destination,
        purpose=args.purpose,
        source=args.source,
        token_mint=args.token_mint,
        token_contract=args.token_contract,
    ).normalize()

    allowlist = CryptoAllowlist(root).load()
    sim = FinancialSimulationEngine(root, allowlist=allowlist).simulate(
        intent,
        balance=args.balance
    )
    validation = FinancialSafetyValidator().validate(sim)
    readiness = MultichainReadiness(root).inspect()
    activation = LiveActivationGate(root).evaluate(readiness, validation)

    print(json.dumps({
        "success": True,
        "intent": intent,
        "simulation": sim,
        "validation": validation,
        "readiness": readiness,
        "activation_gate": activation
    }, indent=2, default=str))

if __name__ == "__main__":
    main()
