#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.walletintegration.transaction_lifecycle import TransactionLifecycleStore

with tempfile.TemporaryDirectory(prefix="phase82_lifecycle_") as td:
    store = TransactionLifecycleStore(Path(td))
    r = store.new(
        wallet_address="WALLET",
        destination="DEST",
        requested_lamports=0,
        balance_before_lamports=10000,
        metadata={"test": True},
    )

    expected = ["AUTHORIZED", "SIGNED", "SUBMITTED", "CONFIRMED", "FINALIZED"]
    observed = [r.state]

    store.transition(r, "SIGNED")
    observed.append(r.state)

    store.transition(r, "SUBMITTED", signature="TEST_SIGNATURE")
    observed.append(r.state)

    store.transition(r, "CONFIRMED", confirmation_status="confirmed", slot=123)
    observed.append(r.state)

    store.transition(r, "FINALIZED", confirmation_status="finalized", balance_after_lamports=5000)
    observed.append(r.state)

    reloaded = store.load(r.lifecycle_id)

    checks = {
        "state_sequence": observed == expected,
        "signature_persisted": reloaded.signature == "TEST_SIGNATURE",
        "finalized_persisted": reloaded.state == "FINALIZED",
        "balance_delta": reloaded.observed_balance_delta_lamports == 5000,
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("PHASE82_LIFECYCLE_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
