from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from companyos.walletintegration.execution_recovery_manager import ExecutionRecoveryManager
from companyos.walletintegration.transaction_lifecycle import TransactionLifecycleStore


@dataclass(frozen=True)
class StartupGateResult:
    allowed_to_resume: bool
    reason: str
    recovered_records: int
    unresolved_records: int
    failed_records: int
    finalized_records: int
    signed_pending_records: int


class StartupReconciliationGate:
    """
    Runs recovery before the execution engine resumes after restart.

    Rules:
    - Always reconcile persisted lifecycle records first.
    - Never auto-rebroadcast SIGNED/AUTHORIZED records.
    - Allow runtime to resume when there are no ambiguous SUBMITTED records.
    - SIGNED/AUTHORIZED records may remain pending safely because they have not
      been submitted and are protected from blind replay.
    """

    def __init__(
        self,
        *,
        rpc_url: str,
        store: TransactionLifecycleStore | None = None,
    ) -> None:
        self.store = store or TransactionLifecycleStore()
        self.recovery = ExecutionRecoveryManager(rpc_url, self.store)

    def evaluate(self) -> StartupGateResult:
        outcomes = self.recovery.recover_all()

        unresolved = 0
        failed = 0
        finalized = 0
        signed_pending = 0

        for p in self.store.root.glob("*.json"):
            try:
                r = self.store.load(p.stem)
            except Exception:
                unresolved += 1
                continue

            if r.state == "FAILED":
                failed += 1
            elif r.state == "FINALIZED":
                finalized += 1
            elif r.state in ("AUTHORIZED", "SIGNED"):
                signed_pending += 1
            elif r.state == "SUBMITTED":
                unresolved += 1

        allowed = unresolved == 0
        reason = (
            "startup_reconciliation_clear"
            if allowed
            else "unresolved_submitted_records_present"
        )

        return StartupGateResult(
            allowed_to_resume=allowed,
            reason=reason,
            recovered_records=len(outcomes),
            unresolved_records=unresolved,
            failed_records=failed,
            finalized_records=finalized,
            signed_pending_records=signed_pending,
        )
