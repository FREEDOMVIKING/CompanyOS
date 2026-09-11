from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any
import json
import time
import uuid


@dataclass(frozen=True)
class LiveAuthorization:
    allowed: bool
    reason: str
    confirmation_required: bool
    confirmation_valid: bool


class LiveExecutionControl:
    """
    Final live-execution gate above the policy gateway.

    Guarantees:
    - dry-run requests never become live implicitly
    - live mode requires an explicit confirmation token
    - token is compared against a local env/config value
    - every authorization decision is written to a durable audit log
    - this layer does not construct/sign transactions itself
    """

    def __init__(
        self,
        *,
        audit_root: Path | None = None,
        required_token: str = "",
    ) -> None:
        self.audit_root = audit_root or (Path.home() / ".companyos_runtime" / "live_execution_control")
        self.audit_root.mkdir(parents=True, exist_ok=True)
        self.required_token = str(required_token or "")

    def authorize(
        self,
        *,
        live_requested: bool,
        provided_token: str = "",
        source: str = "manual",
        metadata: Optional[dict[str, Any]] = None,
    ) -> LiveAuthorization:
        provided_token = str(provided_token or "")

        if not live_requested:
            decision = LiveAuthorization(
                allowed=True,
                reason="dry_run_authorized",
                confirmation_required=False,
                confirmation_valid=False,
            )
            self._write(decision, live_requested, source, metadata)
            return decision

        if not self.required_token:
            decision = LiveAuthorization(
                allowed=False,
                reason="live_confirmation_token_not_configured",
                confirmation_required=True,
                confirmation_valid=False,
            )
            self._write(decision, live_requested, source, metadata)
            return decision

        if provided_token != self.required_token:
            decision = LiveAuthorization(
                allowed=False,
                reason="live_confirmation_token_invalid",
                confirmation_required=True,
                confirmation_valid=False,
            )
            self._write(decision, live_requested, source, metadata)
            return decision

        decision = LiveAuthorization(
            allowed=True,
            reason="live_confirmation_authorized",
            confirmation_required=True,
            confirmation_valid=True,
        )
        self._write(decision, live_requested, source, metadata)
        return decision

    def _write(
        self,
        decision: LiveAuthorization,
        live_requested: bool,
        source: str,
        metadata: Optional[dict[str, Any]],
    ) -> None:
        now = time.time()
        payload = {
            "event_id": str(uuid.uuid4()),
            "created_at_unix": now,
            "live_requested": bool(live_requested),
            "allowed": decision.allowed,
            "reason": decision.reason,
            "confirmation_required": decision.confirmation_required,
            "confirmation_valid": decision.confirmation_valid,
            "source": source,
            "metadata": metadata or {},
        }
        day = time.strftime("%Y-%m-%d", time.localtime(now))
        d = self.audit_root / day
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{int(now*1000)}_{payload['event_id']}.json"
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(path)
