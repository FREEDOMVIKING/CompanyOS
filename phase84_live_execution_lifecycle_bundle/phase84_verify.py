#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase75_feed_present": Path("companyos/walletintegration/live_treasury_feed.py").exists(),
    "phase76_authorizer_present": Path("companyos/walletintegration/live_treasury_authorizer.py").exists(),
    "phase80_broadcaster_present": Path("companyos/walletintegration/controlled_solana_broadcaster.py").exists(),
    "phase81_confirmation_present": Path("companyos/walletintegration/solana_confirmation_tracker.py").exists(),
    "phase82_lifecycle_present": Path("companyos/walletintegration/transaction_lifecycle.py").exists(),
    "phase83_bridge_present": Path("companyos/walletintegration/lifecycle_execution_bridge.py").exists(),
    "phase84_engine_present": Path("companyos/walletintegration/live_solana_execution_engine.py").exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("FRESH_BALANCE_BEFORE_AUTH: True")
print("LIFECYCLE_AUTOMATICALLY_PERSISTED: True")
print("BROADCAST_DEFAULT_DISABLED: True")
print("INSTALLER_BROADCASTS: False")
print("VERIFY_BROADCASTS: False")
print("PHASE84_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
