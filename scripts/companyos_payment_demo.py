#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.paymentops import SandboxPaymentConnector, PaymentOrchestrator
from companyos.treasuryops import TreasuryPolicy

root = Path.home() / "companyos"

policy = TreasuryPolicy(
    autonomous_single_tx_limit=25,
    autonomous_daily_limit=100,
    reserve_floor=250,
    max_daily_loss=50,
    require_allowlist=True,
    allow_autonomous_transfers=True
)

connector = SandboxPaymentConnector(starting_balance=1000)
orch = PaymentOrchestrator(
    root,
    connector,
    allowlist={"sandbox_vendor"},
    policy=policy
)

result = orch.request_transfer(
    amount=10,
    destination="sandbox_vendor",
    purpose="Phase 23000 sandbox verification"
)

print(json.dumps(result, indent=2))
