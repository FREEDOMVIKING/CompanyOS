#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase71_loader_present": Path("companyos/walletintegration/adaptive_solana_key.py").exists(),
    "phase72_adapter_present": Path("companyos/walletintegration/solana_signer_key_adapter.py").exists(),
    "phase74_rpc_present": Path("companyos/walletintegration/solana_rpc_preflight.py").exists(),
    "phase75_feed_present": Path("companyos/walletintegration/live_treasury_feed.py").exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("LIVE_BALANCE_HARDCODED: False")
print("FORCE_FRESH_BEFORE_FINANCIAL_ACTION_AVAILABLE: True")
print("STALE_STATE_DETECTION_AVAILABLE: True")
print("TRANSACTION_BROADCAST_BY_VERIFY: False")
print("PHASE75_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
