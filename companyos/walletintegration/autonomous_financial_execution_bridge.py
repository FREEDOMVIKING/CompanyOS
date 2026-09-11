from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Any
import json, time, uuid


@dataclass(frozen=True)
class AutonomousFinancialAction:
    action_id: str
    action_type: str
    destination: str
    amount_sol: float
    source: str = "autonomous_ceo"
    live_requested: bool = False
    confirm_token: str = ""
    metadata: Optional[dict[str, Any]] = None


@dataclass(frozen=True)
class AutonomousFinancialResult:
    accepted: bool
    reason: str
    mode: str
    action_id: str
    lifecycle_id: Optional[str]
    state: Optional[str]
    signature: Optional[str]
    confirmation_status: Optional[str]


class AutonomousFinancialExecutionBridge:
    """
    Bridge from CEO/autonomous financial intents into the existing controlled
    production SOL gateway.

    This layer NEVER silently upgrades dry-run to live.
    Live execution must already be authorized by LiveExecutionControl.
    """

    def __init__(self, *, gateway, live_control, audit_root: Path | None = None):
        self.gateway = gateway
        self.live_control = live_control
        self.audit_root = audit_root or (
            Path.home() / ".companyos_runtime" / "autonomous_financial_bridge"
        )
        self.audit_root.mkdir(parents=True, exist_ok=True)

    def execute(self, action: AutonomousFinancialAction) -> AutonomousFinancialResult:
        if action.action_type != "sol_transfer":
            return self._finish(action, False, "unsupported_action_type")

        if action.amount_sol <= 0:
            return self._finish(action, False, "amount_must_be_positive")

        auth = self.live_control.authorize(
            live_requested=action.live_requested,
            provided_token=action.confirm_token,
            source=action.source,
            metadata={
                "action_id": action.action_id,
                "action_type": action.action_type,
                "destination": action.destination,
                "amount_sol": action.amount_sol,
                **(action.metadata or {}),
            },
        )

        if not auth.allowed:
            return self._finish(action, False, auth.reason)

        lamports = int(round(action.amount_sol * 1_000_000_000))
        if lamports <= 0:
            return self._finish(action, False, "amount_rounds_to_zero_lamports")

        result = self.gateway.execute(
            destination=action.destination,
            amount_lamports=lamports,
            allow_broadcast=bool(action.live_requested),
            confirm_token=action.confirm_token if action.live_requested else "",
            idempotency_key=f"autonomous:{action.action_id}",
            source=action.source,
        )

        out = AutonomousFinancialResult(
            accepted=bool(result.accepted),
            reason=str(result.reason),
            mode="LIVE" if action.live_requested else "DRY_RUN",
            action_id=action.action_id,
            lifecycle_id=result.lifecycle_id,
            state=result.state,
            signature=result.signature,
            confirmation_status=result.confirmation_status,
        )
        self._write(action, out)
        return out

    def _finish(self, action, accepted, reason):
        out = AutonomousFinancialResult(
            accepted=accepted,
            reason=reason,
            mode="LIVE" if action.live_requested else "DRY_RUN",
            action_id=action.action_id,
            lifecycle_id=None,
            state=None,
            signature=None,
            confirmation_status=None,
        )
        self._write(action, out)
        return out

    def _write(self, action, result):
        now = time.time()
        payload = {
            "event_id": str(uuid.uuid4()),
            "created_at_unix": now,
            "action": {
                "action_id": action.action_id,
                "action_type": action.action_type,
                "destination": action.destination,
                "amount_sol": action.amount_sol,
                "source": action.source,
                "live_requested": action.live_requested,
                "metadata": action.metadata or {},
            },
            "result": asdict(result),
        }
        # Never persist the confirmation token.
        day = time.strftime("%Y-%m-%d", time.localtime(now))
        d = self.audit_root / day
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{int(now*1000)}_{payload['event_id']}.json"
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(p)
