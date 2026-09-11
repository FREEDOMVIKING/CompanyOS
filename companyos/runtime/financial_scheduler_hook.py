from __future__ import annotations

from typing import Any, Optional

from companyos.walletintegration.autonomous_financial_runtime_adapter import (
    execute_runtime_financial_intent,
)


def execute_financial_action_from_scheduler(action: dict[str, Any]):
    """
    Minimal scheduler-facing adapter.

    Expected action keys:
      destination
      amount_sol
      action_id (optional)
      source (optional)
      requested_mode (optional, defaults to dry_run)
      confirm_token (optional)

    This adapter does not guess live mode.
    """
    return execute_runtime_financial_intent(
        destination=str(action.get("destination") or ""),
        amount_sol=float(action.get("amount_sol") or 0.0),
        action_id=str(action.get("action_id") or ""),
        source=str(action.get("source") or "autonomous_scheduler"),
        requested_mode=str(action.get("requested_mode") or "dry_run"),
        confirm_token=str(action.get("confirm_token") or ""),
        metadata=action.get("metadata") or {},
    )
