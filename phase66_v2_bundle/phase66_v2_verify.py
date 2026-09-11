#!/usr/bin/env python3
from __future__ import annotations
import json, tempfile
from pathlib import Path
from companyos.walletintegration.pending_recovery import PendingTransactionRecovery

class FakeRpc:
    def __init__(self, responses):
        self.responses = list(responses)
    def signature_status(self, signature):
        return self.responses.pop(0)

def rv(value):
    return {"success": True, "result": {"value": [value]}}

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    fake = FakeRpc([
        rv({"confirmationStatus": "processed", "err": None}),
        rv({"confirmationStatus": "confirmed", "err": None}),
        rv({"confirmationStatus": "finalized", "err": None}),
        rv({"confirmationStatus": "confirmed", "err": {"InstructionError": [0, "Custom"]}}),
    ])
    r = PendingTransactionRecovery(root=root, rpc=fake)

    a = r.register("TX_PENDING", destination="DEST", amount=0.001)
    b = r.register("TX_PENDING", destination="DEST", amount=0.001)
    c1 = r.reconcile_one("TX_PENDING")
    still = r.status("TX_PENDING") is not None
    c2 = r.reconcile_one("TX_PENDING")
    gone = r.status("TX_PENDING") is None

    r.register("TX_FINALIZED")
    c3 = r.reconcile_one("TX_FINALIZED")

    r.register("TX_FAILED")
    c4 = r.reconcile_one("TX_FAILED")

    checks = {
        "register_success": a.get("success") is True,
        "duplicate_idempotent": b.get("status") == "pending_already_registered",
        "duplicate_never_rebroadcasts": b.get("rebroadcast_performed") is False,
        "processed_is_pending": c1.get("state") == "pending" and still,
        "confirmed_terminal": c2.get("state") == "confirmed" and gone,
        "finalized_terminal": c3.get("state") == "finalized",
        "failed_terminal": c4.get("state") == "failed",
        "never_rebroadcasts": all(x.get("rebroadcast_performed") is False for x in (c1,c2,c3,c4)),
        "history_written": r.history_path.exists() and r.history_path.stat().st_size > 0,
    }
    ok = all(checks.values())
    print("===== PHASE 66 V2 VERIFY =====")
    print(json.dumps(checks, indent=2))
    print("PHASE66_V2_VERIFY:", "PASS" if ok else "FAIL")
    print("TRANSACTION_CREATED_BY_VERIFIER: False")
    print("SIGNING_PERFORMED_BY_VERIFIER: False")
    print("BROADCAST_PERFORMED_BY_VERIFIER: False")
    raise SystemExit(0 if ok else 1)
