#!/usr/bin/env python3
from pathlib import Path
import json

from companyos.walletintegration.solana_rpc_preflight import rpc_call
from companyos.walletintegration.transaction_lifecycle import TransactionLifecycleStore


def load_env():
    candidates = [
        Path.home() / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / ".companyos_runtime" / "live_financial.env",
        Path.home() / "companyos" / "companyos_runtime" / "live_financial.env",
    ]
    p = next((x for x in candidates if x.exists()), None)
    if p is None:
        raise SystemExit("PHASE82_RECONCILE: FAIL - env file not found")
    cfg = {}
    for line in p.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip().strip("'\"")
    return cfg


def newest_lifecycle_file(root: Path):
    files = list(root.glob("*.json"))
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


cfg = load_env()
rpc = cfg.get("SOLANA_RPC_URL", "")
if not rpc:
    raise SystemExit("PHASE82_RECONCILE: FAIL - SOLANA_RPC_URL missing")

store = TransactionLifecycleStore()
latest = newest_lifecycle_file(store.root)

if latest is None:
    print("NO_EXISTING_LIFECYCLE_RECORD: True")
    print("PHASE82_RECONCILE: PASS")
    raise SystemExit(0)

record = store.load(latest.stem)

if not record.signature:
    print("LIFECYCLE_ID:", record.lifecycle_id)
    print("SIGNATURE_PRESENT: False")
    print("STATE:", record.state)
    print("PHASE82_RECONCILE: PASS")
    raise SystemExit(0)

status = rpc_call(
    rpc,
    "getSignatureStatuses",
    [[record.signature], {"searchTransactionHistory": True}],
)
values = (status.get("result") or {}).get("value") or []
item = values[0] if values else None

if not item:
    print("LIFECYCLE_ID:", record.lifecycle_id)
    print("SIGNATURE_PRESENT: True")
    print("STATUS_FOUND: False")
    print("STATE:", record.state)
    print("PHASE82_RECONCILE: PASS")
    raise SystemExit(0)

err = item.get("err")
confirmation = item.get("confirmationStatus")
slot = item.get("slot")

if err is not None:
    new_state = "FAILED"
elif confirmation == "finalized":
    new_state = "FINALIZED"
elif confirmation == "confirmed":
    new_state = "CONFIRMED"
else:
    new_state = record.state

store.transition(
    record,
    new_state,
    status_err=err,
    confirmation_status=confirmation,
    slot=slot,
)

print("LIFECYCLE_ID:", record.lifecycle_id)
print("SIGNATURE_PRESENT: True")
print("STATUS_FOUND: True")
print("CONFIRMATION_STATUS:", confirmation)
print("STATUS_ERR:", err)
print("STATE:", record.state)
print("PHASE82_RECONCILE: PASS")
