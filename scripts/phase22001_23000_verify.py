#!/usr/bin/env python3
import json, tempfile
from pathlib import Path

from companyos.paymentops import SandboxPaymentConnector, PaymentOrchestrator, PaymentOpsStatus
from companyos.treasuryops import TreasuryPolicy

root = Path(tempfile.mkdtemp())

# Safe-default path: real autonomous transfers disabled -> approval queue.
p1 = TreasuryPolicy(
    autonomous_single_tx_limit=25,
    autonomous_daily_limit=100,
    reserve_floor=250,
    max_daily_loss=50,
    require_allowlist=True,
    allow_autonomous_transfers=False
)
c1 = SandboxPaymentConnector(1000)
o1 = PaymentOrchestrator(root, c1, allowlist={"vendor"}, policy=p1)
r1 = o1.request_transfer(amount=10, destination="vendor", purpose="test")
assert r1["status"] == "queued_for_approval"

# Explicit sandbox-autonomy path.
p2 = TreasuryPolicy(
    autonomous_single_tx_limit=25,
    autonomous_daily_limit=100,
    reserve_floor=250,
    max_daily_loss=50,
    require_allowlist=True,
    allow_autonomous_transfers=True
)
c2 = SandboxPaymentConnector(1000)
o2 = PaymentOrchestrator(root, c2, allowlist={"vendor"}, policy=p2)
r2 = o2.request_transfer(amount=10, destination="vendor", purpose="test")
assert r2["status"] == "executed"
assert r2["transaction"]["success"] is True

# Non-allowlisted destination must block.
r3 = o2.request_transfer(amount=10, destination="evil", purpose="test")
assert r3["status"] == "blocked"

s = PaymentOpsStatus().status()
assert s["real_provider_connected"] is False
assert s["real_money_enabled"] is False

print(json.dumps({
    "success":True,
    "status":"phase22001_23000_verification_passed",
    "cycle_status":"phase23000_policy_enforced_financial_execution_framework_ready",
    "real_money_enabled":False
}, indent=2))
