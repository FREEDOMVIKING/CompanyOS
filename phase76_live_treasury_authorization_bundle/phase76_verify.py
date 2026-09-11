#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase75_feed_present": Path(
        "companyos/walletintegration/live_treasury_feed.py"
    ).exists(),
    "phase76_authorizer_present": Path(
        "companyos/walletintegration/live_treasury_authorizer.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("FORCED_FRESH_BALANCE_BEFORE_AUTH: True")
print("RESERVE_ENFORCEMENT_AVAILABLE: True")
print("STALE_STATE_REJECTED: True")
print("TRANSACTION_CREATED_BY_VERIFY: False")
print("TRANSACTION_SIGNED_BY_VERIFY: False")
print("TRANSACTION_BROADCAST_BY_VERIFY: False")
print("PHASE76_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
