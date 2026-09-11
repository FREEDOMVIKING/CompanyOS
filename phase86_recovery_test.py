#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.walletintegration.transaction_lifecycle import TransactionLifecycleStore
from companyos.walletintegration.execution_recovery_manager import ExecutionRecoveryManager


class FakeRecoveryManager(ExecutionRecoveryManager):
    def __init__(self, status_map, store):
        super().__init__("http://example.invalid", store)
        self.status_map = status_map

    def _signature_status(self, signature: str):
        return self.status_map.get(signature)


with tempfile.TemporaryDirectory(prefix="phase86_recovery_") as td:
    store = TransactionLifecycleStore(Path(td))

    # SIGNED with no signature: must not rebroadcast.
    signed = store.new(
        wallet_address="W",
        destination="D",
        requested_lamports=0,
        metadata={"case": "signed"},
    )
    store.transition(signed, "SIGNED")

    # SUBMITTED + confirmed
    confirmed = store.new(
        wallet_address="W",
        destination="D",
        requested_lamports=0,
        metadata={"case": "confirmed"},
    )
    store.transition(confirmed, "SIGNED")
    store.transition(confirmed, "SUBMITTED", signature="SIG_CONFIRMED")

    # SUBMITTED + finalized
    finalized = store.new(
        wallet_address="W",
        destination="D",
        requested_lamports=0,
        metadata={"case": "finalized"},
    )
    store.transition(finalized, "SIGNED")
    store.transition(finalized, "SUBMITTED", signature="SIG_FINALIZED")

    # SUBMITTED + failed
    failed = store.new(
        wallet_address="W",
        destination="D",
        requested_lamports=0,
        metadata={"case": "failed"},
    )
    store.transition(failed, "SIGNED")
    store.transition(failed, "SUBMITTED", signature="SIG_FAILED")

    mgr = FakeRecoveryManager(
        {
            "SIG_CONFIRMED": {
                "confirmationStatus": "confirmed",
                "err": None,
                "slot": 111,
            },
            "SIG_FINALIZED": {
                "confirmationStatus": "finalized",
                "err": None,
                "slot": 222,
            },
            "SIG_FAILED": {
                "confirmationStatus": "confirmed",
                "err": {"InstructionError": [0, "Custom"]},
                "slot": 333,
            },
        },
        store,
    )

    outcomes = {o.lifecycle_id: o for o in mgr.recover_all()}

    checks = {
        "signed_not_rebroadcast": outcomes[signed.lifecycle_id].action == "pending_not_rebroadcast",
        "confirmed_reconciled": store.load(confirmed.lifecycle_id).state == "CONFIRMED",
        "finalized_reconciled": store.load(finalized.lifecycle_id).state == "FINALIZED",
        "failed_reconciled": store.load(failed.lifecycle_id).state == "FAILED",
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("PHASE86_RECOVERY_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
