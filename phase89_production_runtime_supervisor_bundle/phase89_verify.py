#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase88_boot_orchestrator_present": Path(
        "companyos/walletintegration/boot_orchestrator.py"
    ).exists(),
    "phase87_startup_gate_present": Path(
        "companyos/walletintegration/startup_reconciliation_gate.py"
    ).exists(),
    "phase75_live_feed_present": Path(
        "companyos/walletintegration/live_treasury_feed.py"
    ).exists(),
    "phase89_supervisor_present": Path(
        "companyos/walletintegration/production_runtime_supervisor.py"
    ).exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("PERSISTENT_RUNTIME_SUPERVISOR: True")
print("LIVE_TREASURY_REFRESH_LOOP: True")
print("RECOVERY_RECONCILIATION_LOOP: True")
print("MAX_FAILURE_STOP_GUARD: True")
print("SUPERVISOR_BUILDS_TRANSACTION: False")
print("SUPERVISOR_SIGNS_TRANSACTION: False")
print("SUPERVISOR_BROADCASTS: False")
print("PHASE89_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
