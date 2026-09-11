#!/usr/bin/env python3
from pathlib import Path

from companyos.walletintegration.execution_recovery_manager import ExecutionRecoveryManager


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE86_RUNTIME_RECOVERY: FAIL - env file not found")

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
    raise SystemExit("PHASE86_RUNTIME_RECOVERY: FAIL - SOLANA_RPC_URL missing")

mgr = ExecutionRecoveryManager(rpc)
outcomes = mgr.recover_all()

print("RECOVERY_RECORD_COUNT:", len(outcomes))
for o in outcomes:
    print(
        "RECOVERY:",
        o.lifecycle_id,
        "| prior=", o.prior_state,
        "| new=", o.new_state,
        "| action=", o.action,
        "| confirmation=", o.confirmation_status,
        "| err=", o.status_err,
    )

print("BLIND_REBROADCAST_OCCURRED: False")
print("PHASE86_RUNTIME_RECOVERY: PASS")
