#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.walletintegration.transaction_lifecycle import TransactionLifecycleStore
from companyos.walletintegration.startup_reconciliation_gate import StartupReconciliationGate


class FakeGate(StartupReconciliationGate):
    def __init__(self, store):
        self.store = store

        class FakeRecovery:
            def recover_all(self):
                return []

        self.recovery = FakeRecovery()


with tempfile.TemporaryDirectory(prefix="phase87_startup_") as td:
    store = TransactionLifecycleStore(Path(td))

    # Safe pending SIGNED record: should not block startup.
    r1 = store.new(
        wallet_address="W",
        destination="D",
        requested_lamports=0,
        metadata={"case": "signed_pending"},
    )
    store.transition(r1, "SIGNED")

    gate = FakeGate(store)
    result1 = gate.evaluate()

    # Ambiguous SUBMITTED record should block resume.
    r2 = store.new(
        wallet_address="W",
        destination="D",
        requested_lamports=0,
        metadata={"case": "submitted_pending"},
    )
    store.transition(r2, "SIGNED")
    store.transition(r2, "SUBMITTED", signature="SIG_UNKNOWN")

    result2 = gate.evaluate()

    checks = {
        "signed_pending_does_not_block": result1.allowed_to_resume is True,
        "submitted_pending_blocks": result2.allowed_to_resume is False,
        "unresolved_count_detected": result2.unresolved_records == 1,
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("PHASE87_STARTUP_GATE_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
