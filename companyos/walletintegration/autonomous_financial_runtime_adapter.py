from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any
import os
import uuid

from companyos.walletintegration.autonomous_financial_bridge_factory import (
    build_autonomous_financial_bridge,
)
from companyos.walletintegration.autonomous_financial_execution_bridge import (
    AutonomousFinancialAction,
    AutonomousFinancialResult,
)


@dataclass(frozen=True)
class RuntimeFinancialIntent:
    destination: str
    amount_sol: float
    action_id: str = ""
    source: str = "autonomous_runtime"
    requested_mode: str = "dry_run"
    confirm_token: str = ""
    metadata: Optional[dict[str, Any]] = None


class AutonomousFinancialRuntimeAdapter:
    """
    Stable internal runtime entry point for CompanyOS scheduler/CEO actions.

    Important:
    - default mode is DRY RUN
    - live mode is never inferred
    - live mode requires requested_mode == "live"
    - live authorization remains enforced downstream by LiveExecutionControl
    """

    def __init__(self):
        self.bridge = build_autonomous_financial_bridge()

    def execute(self, intent: RuntimeFinancialIntent) -> AutonomousFinancialResult:
        mode = str(intent.requested_mode or "dry_run").strip().lower()

        if mode not in {"dry_run", "live"}:
            raise ValueError(f"unsupported_requested_mode:{mode}")

        action = AutonomousFinancialAction(
            action_id=intent.action_id or str(uuid.uuid4()),
            action_type="sol_transfer",
            destination=str(intent.destination).strip(),
            amount_sol=float(intent.amount_sol),
            source=str(intent.source or "autonomous_runtime"),
            live_requested=(mode == "live"),
            confirm_token=str(intent.confirm_token or ""),
            metadata=intent.metadata or {},
        )

        return self.bridge.execute(action)


def execute_runtime_financial_intent(
    *,
    destination: str,
    amount_sol: float,
    action_id: str = "",
    source: str = "autonomous_runtime",
    requested_mode: str = "dry_run",
    confirm_token: str = "",
    metadata: Optional[dict[str, Any]] = None,
) -> AutonomousFinancialResult:
    return AutonomousFinancialRuntimeAdapter().execute(
        RuntimeFinancialIntent(
            destination=destination,
            amount_sol=amount_sol,
            action_id=action_id,
            source=source,
            requested_mode=requested_mode,
            confirm_token=confirm_token,
            metadata=metadata,
        )
    )
