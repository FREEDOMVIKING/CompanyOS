#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.ceofinops import CEOFinancialDecisionLoop
from companyos.cryptoops import CryptoAllowlist
from companyos.treasuryops import TreasuryPolicy

root = Path.home() / "companyos"
loop = CEOFinancialDecisionLoop(
    root,
    allowlist=CryptoAllowlist(root).load(),
    policy=TreasuryPolicy.from_env(),
)

opportunities = [
    {
        "name":"Example low-risk growth experiment",
        "required_capital":10,
        "expected_return":20,
        "confidence":0.7,
        "risk":0.15,
        "destination":"sandbox_vendor",
        "chain":"solana",
        "purpose":"dry-run growth experiment"
    },
    {
        "name":"Example weaker opportunity",
        "required_capital":25,
        "expected_return":10,
        "confidence":0.4,
        "risk":0.5,
        "destination":"sandbox_vendor",
        "chain":"solana",
        "purpose":"dry-run weak opportunity"
    }
]

result = loop.evaluate_opportunities(
    opportunities,
    available_capital=1000,
    reserve_floor=250,
)

print(json.dumps(result, indent=2))
