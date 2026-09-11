#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.businessops import AutonomousBusinessLoop
from companyos.ceofinops import CEOFinancialDecisionLoop
from companyos.cryptoops import CryptoAllowlist
from companyos.treasuryops import TreasuryPolicy

root = Path.home() / "companyos"

fin = CEOFinancialDecisionLoop(
    root,
    allowlist=CryptoAllowlist(root).load(),
    policy=TreasuryPolicy.from_env()
)
loop = AutonomousBusinessLoop(root, ceo_finance_loop=fin)

candidates = [
    {
        "id":"venture_a",
        "name":"AI service validation venture",
        "expected_value":100,
        "confidence":0.7,
        "risk":0.2,
        "effort":0.3,
        "required_capital":10,
        "expected_return":30,
        "destination":"sandbox_vendor",
        "chain":"solana",
        "requires_launch_approval":True
    },
    {
        "id":"venture_b",
        "name":"Higher risk experiment",
        "expected_value":80,
        "confidence":0.4,
        "risk":0.7,
        "effort":0.6,
        "required_capital":20,
        "expected_return":25,
        "destination":"sandbox_vendor",
        "chain":"solana",
        "requires_launch_approval":True
    }
]

result = loop.evaluate(
    candidates,
    build_result={"success":True},
    available_capital=1000,
    reserve_floor=250
)
print(json.dumps(result, indent=2))
