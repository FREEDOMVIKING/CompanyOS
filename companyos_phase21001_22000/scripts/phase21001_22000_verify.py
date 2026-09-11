#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.treasuryops import TreasuryPolicy, SpendController, TreasuryReconciler, TreasuryStatus
from companyos.runtimeops import RuntimeCheckpoint, RuntimeHealth

root = Path(tempfile.mkdtemp())
policy = TreasuryPolicy(
    autonomous_single_tx_limit=25,
    autonomous_daily_limit=100,
    reserve_floor=250,
    max_daily_loss=50,
    require_allowlist=True,
    allow_autonomous_transfers=False
)
ctl = SpendController(root, policy=policy)

d1 = ctl.authorize(
    amount=10,
    balance=1000,
    destination="vendor_a",
    allowlist={"vendor_a"},
    daily_loss=0,
    purpose="test"
)
assert d1["decision"] == "approval_required"

policy2 = TreasuryPolicy(
    autonomous_single_tx_limit=25,
    autonomous_daily_limit=100,
    reserve_floor=250,
    max_daily_loss=50,
    require_allowlist=True,
    allow_autonomous_transfers=True
)
ctl2 = SpendController(root, policy=policy2)
d2 = ctl2.authorize(
    amount=10,
    balance=1000,
    destination="vendor_a",
    allowlist={"vendor_a"},
    daily_loss=0,
    purpose="test"
)
assert d2["decision"] == "autonomous_allowed"

d3 = ctl2.authorize(
    amount=800,
    balance=1000,
    destination="vendor_a",
    allowlist={"vendor_a"},
    daily_loss=0,
    purpose="unsafe"
)
assert d3["decision"] == "blocked"

rec = TreasuryReconciler().reconcile(
    [{"tx_id":"a"}],
    [{"tx_id":"a"}]
)
assert rec["balanced"] is True

cp = RuntimeCheckpoint(root)
cp.save({"cycle":1})
assert cp.load()["payload"]["cycle"] == 1
assert RuntimeHealth(root).snapshot()["runtime_exists"] is True
assert TreasuryStatus().status()["status"] == "phase22000_autonomous_treasury_safety_kernel_ready"

print(json.dumps({
    "success": True,
    "status": "phase21001_22000_verification_passed",
    "cycle_status": "phase22000_persistent_autonomy_and_treasury_safety_ready",
    "safe_default_autonomous_transfers": False
}, indent=2))
