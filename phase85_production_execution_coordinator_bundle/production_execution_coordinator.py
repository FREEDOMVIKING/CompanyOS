from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any

from companyos.walletintegration.live_solana_execution_engine import (
    LiveSolanaExecutionEngine,
    LiveExecutionResult,
)
from companyos.walletintegration.transaction_lifecycle import TransactionLifecycleStore


@dataclass(frozen=True)
class ProductionExecutionRequest:
    action_type: str
    amount_lamports: int
    destination: str
    allow_broadcast: bool
    confirm_token: str = ""


@dataclass(frozen=True)
class ProductionExecutionResponse:
    accepted: bool
    reason: str
    lifecycle_id: Optional[str]
    state: Optional[str]
    signature: Optional[str]
    success: bool
    confirmation_status: Optional[str]
    status_err: Any


class ProductionExecutionCoordinator:
    """
    Single controlled entry point for production financial execution.

    Current live-supported action:
      zero_lamport_self_transfer

    Guarantees:
    - Rejects unsupported action types.
    - Rejects negative amounts.
    - Requires amount=0 and destination=self for the validation action.
    - Delegates live balance/auth/build/sign/broadcast/confirm/reconcile
      to LiveSolanaExecutionEngine.
    - Prevents accidental duplicate replays by checking lifecycle records
      for matching idempotency_key metadata when supplied.
    """

    def __init__(
        self,
        *,
        engine: LiveSolanaExecutionEngine,
        lifecycle_store: TransactionLifecycleStore | None = None,
    ) -> None:
        self.engine = engine
        self.store = lifecycle_store or TransactionLifecycleStore()

    def _find_existing_by_idempotency_key(self, key: str):
        if not key:
            return None
        for p in self.store.root.glob("*.json"):
            try:
                record = self.store.load(p.stem)
                if (record.metadata or {}).get("idempotency_key") == key:
                    return record
            except Exception:
                continue
        return None

    def execute(
        self,
        request: ProductionExecutionRequest,
        *,
        idempotency_key: str = "",
    ) -> ProductionExecutionResponse:

        if request.action_type != "zero_lamport_self_transfer":
            return ProductionExecutionResponse(
                False, "unsupported_action_type", None, None, None,
                False, None, "unsupported_action_type"
            )

        if request.amount_lamports < 0:
            return ProductionExecutionResponse(
                False, "negative_amount_rejected", None, None, None,
                False, None, "negative_amount_rejected"
            )

        if request.amount_lamports != 0:
            return ProductionExecutionResponse(
                False, "validation_action_requires_zero_lamports",
                None, None, None, False, None,
                "validation_action_requires_zero_lamports"
            )

        if request.destination != self.engine.wallet_address:
            return ProductionExecutionResponse(
                False, "validation_action_requires_self_destination",
                None, None, None, False, None,
                "validation_action_requires_self_destination"
            )

        existing = self._find_existing_by_idempotency_key(idempotency_key)
        if existing is not None:
            return ProductionExecutionResponse(
                accepted=False,
                reason="duplicate_idempotency_key",
                lifecycle_id=existing.lifecycle_id,
                state=existing.state,
                signature=existing.signature,
                success=existing.state in ("CONFIRMED", "FINALIZED"),
                confirmation_status=existing.confirmation_status,
                status_err=existing.status_err,
            )

        result: LiveExecutionResult = self.engine.execute_zero_self_transfer(
            allow_broadcast=request.allow_broadcast,
            confirm_token=request.confirm_token,
        )

        # Attach idempotency metadata to the created record.
        if idempotency_key and result.lifecycle_id:
            try:
                record = self.store.load(result.lifecycle_id)
                record.metadata = dict(record.metadata or {})
                record.metadata["idempotency_key"] = idempotency_key
                self.store.save(record)
            except Exception:
                pass

        return ProductionExecutionResponse(
            accepted=True,
            reason=result.reason,
            lifecycle_id=result.lifecycle_id,
            state=result.state,
            signature=result.signature,
            success=result.success,
            confirmation_status=result.confirmation_status,
            status_err=result.status_err,
        )
