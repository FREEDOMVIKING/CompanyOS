from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any

from companyos.walletintegration.solana_rpc_preflight import rpc_call
from companyos.walletintegration.transaction_lifecycle import (
    TransactionLifecycleStore,
    TransactionLifecycleRecord,
)


@dataclass(frozen=True)
class RecoveryOutcome:
    lifecycle_id: str
    prior_state: str
    new_state: str
    action: str
    signature: Optional[str]
    confirmation_status: Optional[str]
    status_err: Any


class ExecutionRecoveryManager:
    """
    Crash/restart recovery for persisted transaction lifecycle records.

    Safety rules:
    - AUTHORIZED/SIGNED records are never blindly rebroadcast.
    - SUBMITTED records with a signature are reconciled on-chain first.
    - CONFIRMED records can be promoted to FINALIZED if chain says finalized.
    - FAILED/FINALIZED records are terminal.
    """

    def __init__(
        self,
        rpc_url: str,
        store: TransactionLifecycleStore | None = None,
    ) -> None:
        self.rpc_url = rpc_url
        self.store = store or TransactionLifecycleStore()

    def _signature_status(self, signature: str):
        data = rpc_call(
            self.rpc_url,
            "getSignatureStatuses",
            [[signature], {"searchTransactionHistory": True}],
        )
        values = (data.get("result") or {}).get("value") or []
        return values[0] if values else None

    def recover_record(self, record: TransactionLifecycleRecord) -> RecoveryOutcome:
        prior = record.state

        if prior in ("FINALIZED", "FAILED"):
            return RecoveryOutcome(
                record.lifecycle_id,
                prior,
                prior,
                "terminal_noop",
                record.signature,
                record.confirmation_status,
                record.status_err,
            )

        if prior in ("AUTHORIZED", "SIGNED") and not record.signature:
            # Important: do not rebroadcast or guess. Leave pending for operator/engine retry policy.
            return RecoveryOutcome(
                record.lifecycle_id,
                prior,
                prior,
                "pending_not_rebroadcast",
                None,
                record.confirmation_status,
                record.status_err,
            )

        if not record.signature:
            return RecoveryOutcome(
                record.lifecycle_id,
                prior,
                prior,
                "signature_missing_noop",
                None,
                record.confirmation_status,
                record.status_err,
            )

        status = self._signature_status(record.signature)

        if not status:
            return RecoveryOutcome(
                record.lifecycle_id,
                prior,
                prior,
                "signature_not_found_no_rebroadcast",
                record.signature,
                record.confirmation_status,
                record.status_err,
            )

        err = status.get("err")
        confirmation = status.get("confirmationStatus")
        slot = status.get("slot")

        if err is not None:
            self.store.transition(
                record,
                "FAILED",
                status_err=err,
                confirmation_status=confirmation,
                slot=slot,
            )
            return RecoveryOutcome(
                record.lifecycle_id,
                prior,
                record.state,
                "reconciled_failed",
                record.signature,
                confirmation,
                err,
            )

        if confirmation == "finalized":
            self.store.transition(
                record,
                "FINALIZED",
                status_err=None,
                confirmation_status=confirmation,
                slot=slot,
            )
            return RecoveryOutcome(
                record.lifecycle_id,
                prior,
                record.state,
                "reconciled_finalized",
                record.signature,
                confirmation,
                None,
            )

        if confirmation == "confirmed":
            self.store.transition(
                record,
                "CONFIRMED",
                status_err=None,
                confirmation_status=confirmation,
                slot=slot,
            )
            return RecoveryOutcome(
                record.lifecycle_id,
                prior,
                record.state,
                "reconciled_confirmed",
                record.signature,
                confirmation,
                None,
            )

        return RecoveryOutcome(
            record.lifecycle_id,
            prior,
            prior,
            "pending_chain_status_no_rebroadcast",
            record.signature,
            confirmation,
            err,
        )

    def recover_all(self) -> list[RecoveryOutcome]:
        outcomes: list[RecoveryOutcome] = []
        for p in sorted(self.store.root.glob("*.json")):
            try:
                record = self.store.load(p.stem)
                outcomes.append(self.recover_record(record))
            except Exception as exc:
                outcomes.append(
                    RecoveryOutcome(
                        p.stem,
                        "UNKNOWN",
                        "UNKNOWN",
                        f"recovery_error:{type(exc).__name__}",
                        None,
                        None,
                        str(exc)[:240],
                    )
                )
        return outcomes
