from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from companyos.walletintegration.live_treasury_authorizer import LiveTreasuryAuthorizer


@dataclass(frozen=True)
class ExecutionGateTreasuryResult:
    allowed: bool
    reason: str
    requested_sol: float
    balance_sol: float
    spendable_sol: float
    reserve_sol: float
    rpc_ok: bool
    stale: bool


class ExecutionGateTreasuryBridge:
    """
    Bridges the execution gate to the live-treasury authorizer.

    This module performs authorization only.
    It does not construct, sign, or broadcast transactions.
    """

    def __init__(self, authorizer: LiveTreasuryAuthorizer) -> None:
        self.authorizer = authorizer

    def authorize_execution(self, amount_sol: float, payload: dict[str, Any] | None = None) -> ExecutionGateTreasuryResult:
        decision = self.authorizer.authorize_sol(float(amount_sol))

        return ExecutionGateTreasuryResult(
            allowed=decision.allowed,
            reason=decision.reason,
            requested_sol=decision.requested_sol,
            balance_sol=decision.current_balance_sol,
            spendable_sol=decision.spendable_sol,
            reserve_sol=decision.reserve_sol,
            rpc_ok=decision.rpc_ok,
            stale=decision.stale,
        )
