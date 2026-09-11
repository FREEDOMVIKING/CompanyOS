#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from companyos.walletintegration.pending_recovery import PendingTransactionRecovery
from companyos.walletintegration.reconciliation_worker import PendingReconciliationWorker


class FakeRpc:
    def __init__(self, responses):
        self.responses = list(responses)

    def signature_status(self, signature):
        if not self.responses:
            raise AssertionError("No fake RPC response left")
        return self.responses.pop(0)


def rv(value):
    return {"success": True, "result": {"value": [value]}}


with tempfile.TemporaryDirectory() as td:
    root = Path(td)

    # Seed three pending entries.
    seed = PendingTransactionRecovery(root=root, rpc=FakeRpc([]))
    seed.register("TX_PENDING", destination="D1", amount=0.001)
    seed.register("TX_CONFIRMED", destination="D2", amount=0.002)
    seed.register("TX_FAILED", destination="D3", amount=0.003)

    fake = FakeRpc([
        rv({"confirmationStatus": "processed", "err": None}),
        rv({"confirmationStatus": "confirmed", "err": None}),
        rv({"confirmationStatus": "confirmed", "err": {"InstructionError": [0, "Custom"]}}),
    ])

    worker = PendingReconciliationWorker(root=root, rpc=fake, stale_after_seconds=0)

    before = worker.inspect()
    result = worker.run_once(limit=100)
    after = worker.inspect()

    checks = {
        "before_count_3": before.get("pending_count") == 3,
        "stale_detection": before.get("stale_count") == 3,
        "worker_success": result.get("success") is True,
        "never_rebroadcasts": result.get("rebroadcast_performed") is False,
        "pending_left_1": after.get("pending_count") == 1,
        "status_file_written": worker.status_path.exists(),
        "history_written": seed.history_path.exists() and seed.history_path.stat().st_size > 0,
    }

    ok = all(checks.values())
    print("===== PHASE 67 V2 VERIFY =====")
    print(json.dumps(checks, indent=2))
    print("PHASE67_V2_VERIFY:", "PASS" if ok else "FAIL")
    print("TRANSACTION_CREATED_BY_VERIFIER: False")
    print("SIGNING_PERFORMED_BY_VERIFIER: False")
    print("BROADCAST_PERFORMED_BY_VERIFIER: False")
    raise SystemExit(0 if ok else 1)
