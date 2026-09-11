#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.walletintegration.transaction_lifecycle import TransactionLifecycleStore
from companyos.walletintegration.lifecycle_execution_bridge import LifecycleExecutionBridge

with tempfile.TemporaryDirectory(prefix="phase83_pipeline_") as td:
    store = TransactionLifecycleStore(Path(td))
    bridge = LifecycleExecutionBridge(store)

    ctx = bridge.begin(
        wallet_address="WALLET",
        destination="DEST",
        requested_lamports=0,
        balance_before_lamports=100000,
        metadata={"mode": "phase83_test"},
    )

    sequence = [ctx.record.state]
    bridge.mark_signed(ctx)
    sequence.append(ctx.record.state)
    bridge.mark_submitted(ctx, "TEST_SIGNATURE")
    sequence.append(ctx.record.state)
    bridge.mark_confirmed(
        ctx,
        confirmation_status="confirmed",
        slot=123,
        status_err=None,
    )
    sequence.append(ctx.record.state)
    bridge.mark_finalized(
        ctx,
        confirmation_status="finalized",
        slot=124,
        balance_after_lamports=95000,
    )
    sequence.append(ctx.record.state)

    reloaded = store.load(ctx.record.lifecycle_id)

    checks = {
        "sequence": sequence == [
            "AUTHORIZED",
            "SIGNED",
            "SUBMITTED",
            "CONFIRMED",
            "FINALIZED",
        ],
        "signature_persisted": reloaded.signature == "TEST_SIGNATURE",
        "final_state": reloaded.state == "FINALIZED",
        "delta_persisted": reloaded.observed_balance_delta_lamports == 5000,
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("PHASE83_PIPELINE_LIFECYCLE_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
