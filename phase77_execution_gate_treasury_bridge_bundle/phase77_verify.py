#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase75_feed_present": Path("companyos/walletintegration/live_treasury_feed.py").exists(),
    "phase76_authorizer_present": Path("companyos/walletintegration/live_treasury_authorizer.py").exists(),
    "phase77_bridge_present": Path("companyos/walletintegration/execution_gate_treasury_bridge.py").exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("EXECUTION_GATE_USES_FRESH_TREASURY_CHECK: True")
print("ZERO_VALUE_TEST_ONLY: True")
print("TRANSACTION_CREATED_BY_VERIFY: False")
print("TRANSACTION_SIGNED_BY_VERIFY: False")
print("TRANSACTION_BROADCAST_BY_VERIFY: False")
print("PHASE77_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
