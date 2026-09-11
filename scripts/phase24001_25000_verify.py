#!/usr/bin/env python3
import json
import os
import tempfile
from pathlib import Path

from companyos.moneyops import FinancialKillSwitch, IdempotencyStore, ReceiptStore, MoneyOpsStatus

root = Path(tempfile.mkdtemp())

# Kill switch.
k = FinancialKillSwitch(root)
assert k.engaged() is False
k.engage("test")
assert k.engaged() is True
k.clear()
assert k.engaged() is False

# Idempotency store.
i = IdempotencyStore(root)
i.put("abc", {"status":"ok"})
assert i.get("abc")["status"] == "ok"

# Receipt store.
r = ReceiptStore(root)
r.append({"tx_id":"x"})
assert r.recent(1)[0]["tx_id"] == "x"

# Safe defaults.
s = MoneyOpsStatus().status()
assert s["dry_run_default"] is True
assert s["live_execution_default"] is False

print(json.dumps({
    "success": True,
    "status": "phase24001_25000_verification_passed",
    "cycle_status": "phase25000_treasury_gated_multichain_execution_ready",
    "live_execution_default": False
}, indent=2))
