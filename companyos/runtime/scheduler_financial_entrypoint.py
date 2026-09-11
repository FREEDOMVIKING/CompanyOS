from __future__ import annotations
from typing import Any
from companyos.runtime.scheduler_financial_intent_dispatcher import SchedulerFinancialIntent, SchedulerFinancialIntentDispatcher
from companyos.runtime.scheduler_financial_activity_bridge import SchedulerFinancialActivityLedgerBridge

def dispatch_scheduler_financial_intent(action: dict[str, Any]):
    intent = SchedulerFinancialIntent(
        destination=str(action.get("destination") or ""),
        amount_sol=float(action.get("amount_sol") or 0.0),
        action_id=str(action.get("action_id") or ""),
        source=str(action.get("source") or "autonomous_scheduler"),
        requested_mode=str(action.get("requested_mode") or "dry_run"),
        confirm_token=str(action.get("confirm_token") or ""),
        metadata=action.get("metadata") or {},
    )
    result = SchedulerFinancialIntentDispatcher().dispatch(intent)
    SchedulerFinancialActivityLedgerBridge().record(
        intent={
            "destination": intent.destination,
            "amount_sol": intent.amount_sol,
            "action_id": result.action_id,
            "source": intent.source,
            "requested_mode": result.requested_mode,
            "metadata": intent.metadata or {},
        },
        result={
            "accepted": result.accepted,
            "reason": result.reason,
            "state": result.state,
            "signature": result.signature,
            "lifecycle_id": result.lifecycle_id,
            "confirmation_status": result.confirmation_status,
        },
    )
    return result
