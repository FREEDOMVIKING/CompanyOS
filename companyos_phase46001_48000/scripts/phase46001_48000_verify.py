#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.transactionops import TransactionPolicy, BalanceAndFeeGuard, DuplicatePaymentGuard, TransactionOpsStatus

p = TransactionPolicy(max_single_amount=1, min_reserve=0.1)
assert p.validate(0.5, "A", {"A"})["allowed"] is True
assert p.validate(2, "A", {"A"})["allowed"] is False
assert p.validate(0.5, "B", {"A"})["allowed"] is False

b = BalanceAndFeeGuard()
assert b.validate(10, 1, 0.1, 1)["allowed"] is True
assert b.validate(1, 0.5, 0.1, 0.5)["allowed"] is False

root = Path(tempfile.mkdtemp())
d = DuplicatePaymentGuard(root)
fp = d.fingerprint("S","D",1,None,"x")
assert d.seen(fp) is False
d.record(fp, {"test":True})
assert d.seen(fp) is True

status = TransactionOpsStatus().status()
assert status["broadcast_auto_enabled"] is False

print(json.dumps({
    "success":True,
    "status":"phase46001_48000_verification_passed",
    "cycle_status":"phase48000_transaction_lifecycle_ready"
}, indent=2))
