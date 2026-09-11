from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os
import time
import uuid

from companyos.walletintegration.execution_policy import (
    ExecutionPolicy,
    ExecutionAuditLedger,
    SolTransferExecutionPolicy,
)
from companyos.walletintegration.production_execution_coordinator import (
    ProductionExecutionCoordinator,
    ProductionExecutionRequest,
)


@dataclass(frozen=True)
class GatewayResult:
    accepted: bool
    reason: str
    state: Optional[str]
    signature: Optional[str]
    lifecycle_id: Optional[str]
    confirmation_status: Optional[str]


class ControlledProductionSolGateway:
    """
    Policy-controlled entry point above ProductionExecutionCoordinator.

    This gateway never bypasses the coordinator, simulator, treasury authorizer,
    broadcaster gates, confirmation tracker, lifecycle store, or idempotency.
    """

    def __init__(
        self,
        *,
        coordinator: ProductionExecutionCoordinator,
        wallet_address: str,
        policy: ExecutionPolicy,
        ledger: ExecutionAuditLedger | None = None,
        allowlist_path: Path | None = None,
    ) -> None:
        self.coordinator = coordinator
        self.wallet_address = wallet_address
        self.ledger = ledger or ExecutionAuditLedger()
        self.policy = SolTransferExecutionPolicy(
            policy,
            wallet_address=wallet_address,
            allowlist_path=allowlist_path,
            ledger=self.ledger,
        )

    def execute(
        self,
        *,
        destination: str,
        amount_lamports: int,
        allow_broadcast: bool = False,
        confirm_token: str = "",
        idempotency_key: str = "",
        source: str = "manual",
    ) -> GatewayResult:
        decision = self.policy.evaluate(destination, amount_lamports)

        self.ledger.append({
            "event_type": "policy_decision",
            "allowed": decision.allowed,
            "reason": decision.reason,
            "amount_sol": decision.amount_sol,
            "amount_lamports": decision.amount_lamports,
            "destination": decision.destination,
            "spent_today_sol": decision.spent_today_sol,
            "remaining_daily_sol": decision.remaining_daily_sol,
            "broadcast_requested": bool(allow_broadcast),
            "source": source,
            "idempotency_key": idempotency_key or None,
        })

        if not decision.allowed:
            return GatewayResult(False, decision.reason, None, None, None, None)

        request = ProductionExecutionRequest(
            action_type="sol_transfer",
            amount_lamports=int(amount_lamports),
            destination=destination,
            allow_broadcast=bool(allow_broadcast),
            confirm_token=confirm_token,
        )

        key = idempotency_key or f"sol-gateway-{uuid.uuid4()}"
        result = self.coordinator.execute(
            request=request,
            idempotency_key=key,
        )

        event_type = (
            "transfer_finalized"
            if result.success and result.signature
            else "transfer_dryrun"
            if result.success and not result.signature
            else "transfer_failed"
        )

        self.ledger.append({
            "event_type": event_type,
            "accepted": result.accepted,
            "reason": result.reason,
            "state": result.state,
            "success": result.success,
            "signature": result.signature,
            "confirmation_status": result.confirmation_status,
            "status_err": result.status_err,
            "amount_sol": decision.amount_sol,
            "amount_lamports": decision.amount_lamports,
            "destination": decision.destination,
            "broadcast_requested": bool(allow_broadcast),
            "source": source,
            "idempotency_key": key,
            "lifecycle_id": result.lifecycle_id,
        })

        return GatewayResult(
            accepted=result.accepted,
            reason=result.reason,
            state=result.state,
            signature=result.signature,
            lifecycle_id=result.lifecycle_id,
            confirmation_status=result.confirmation_status,
        )
