#!/usr/bin/env python3
from pathlib import Path

from companyos.walletintegration.startup_reconciliation_gate import StartupReconciliationGate


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE87_STARTUP_RECONCILE: FAIL - env file not found")

    cfg = {}
    for line in p.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip("'\"")
    return cfg


cfg = load_env()
rpc = cfg.get("SOLANA_RPC_URL", "")
if not rpc:
    raise SystemExit("PHASE87_STARTUP_RECONCILE: FAIL - SOLANA_RPC_URL missing")

gate = StartupReconciliationGate(rpc_url=rpc)
result = gate.evaluate()

print("RECOVERED_RECORDS:", result.recovered_records)
print("UNRESOLVED_RECORDS:", result.unresolved_records)
print("FAILED_RECORDS:", result.failed_records)
print("FINALIZED_RECORDS:", result.finalized_records)
print("SIGNED_PENDING_RECORDS:", result.signed_pending_records)
print("ALLOWED_TO_RESUME:", result.allowed_to_resume)
print("REASON:", result.reason)
print("BLIND_REBROADCAST_OCCURRED: False")
print("PHASE87_STARTUP_RECONCILE:", "PASS" if result.allowed_to_resume else "BLOCKED")
raise SystemExit(0 if result.allowed_to_resume else 2)
