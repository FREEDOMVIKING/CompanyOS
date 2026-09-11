from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any

from companyos.walletintegration.transaction_lifecycle import (
    TransactionLifecycleStore,
    TransactionLifecycleRecord,
)


@dataclass
class LifecycleExecutionContext:
    record: TransactionLifecycleRecord
    store: TransactionLifecycleStore


class LifecycleExecutionBridge:
    """
    Helper used by the execution pipeline to persist lifecycle state changes.

    It does not build, sign, or broadcast transactions itself.
    """

    def __init__(self, store: TransactionLifecycleStore | None = None) -> None:
        self.store = store or TransactionLifecycleStore()

    def begin(
        self,
        *,
        wallet_address: str,
        destination: str,
        requested_lamports: int,
        balance_before_lamports: Optional[int],
        metadata: Optional[dict[str, Any]] = None,
    ) -> LifecycleExecutionContext:
        record = self.store.new(
            wallet_address=wallet_address,
            destination=destination,
            requested_lamports=requested_lamports,
            balance_before_lamports=balance_before_lamports,
            metadata=metadata or {},
        )
        return LifecycleExecutionContext(record=record, store=self.store)

    def mark_signed(self, ctx: LifecycleExecutionContext) -> TransactionLifecycleRecord:
        return ctx.store.transition(ctx.record, "SIGNED")

    def mark_submitted(
        self,
        ctx: LifecycleExecutionContext,
        signature: str,
    ) -> TransactionLifecycleRecord:
        return ctx.store.transition(
            ctx.record,
            "SUBMITTED",
            signature=signature,
        )

    def mark_confirmed(
        self,
        ctx: LifecycleExecutionContext,
        *,
        confirmation_status: str,
        slot: Optional[int],
        status_err: Any = None,
    ) -> TransactionLifecycleRecord:
        return ctx.store.transition(
            ctx.record,
            "CONFIRMED",
            confirmation_status=confirmation_status,
            slot=slot,
            status_err=status_err,
        )

    def mark_finalized(
        self,
        ctx: LifecycleExecutionContext,
        *,
        confirmation_status: str,
        slot: Optional[int],
        balance_after_lamports: Optional[int],
    ) -> TransactionLifecycleRecord:
        return ctx.store.transition(
            ctx.record,
            "FINALIZED",
            confirmation_status=confirmation_status,
            slot=slot,
            balance_after_lamports=balance_after_lamports,
        )

    def mark_failed(
        self,
        ctx: LifecycleExecutionContext,
        *,
        error: Any,
        confirmation_status: Optional[str] = None,
        slot: Optional[int] = None,
        balance_after_lamports: Optional[int] = None,
    ) -> TransactionLifecycleRecord:
        return ctx.store.transition(
            ctx.record,
            "FAILED",
            status_err=error,
            confirmation_status=confirmation_status,
            slot=slot,
            balance_after_lamports=balance_after_lamports,
        )
