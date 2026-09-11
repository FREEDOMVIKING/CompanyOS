from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Any
import json, time, uuid
from companyos.runtime.financial_scheduler_hook import execute_financial_action_from_scheduler

@dataclass(frozen=True)
class SchedulerFinancialIntent:
    destination: str
    amount_sol: float
    action_id: str = ""
    source: str = "autonomous_scheduler"
    requested_mode: str = "dry_run"
    confirm_token: str = ""
    metadata: Optional[dict[str, Any]] = None

@dataclass(frozen=True)
class SchedulerFinancialDispatchResult:
    accepted: bool
    reason: str
    action_id: str
    requested_mode: str
    state: Optional[str]
    signature: Optional[str]
    lifecycle_id: Optional[str]
    confirmation_status: Optional[str]

class SchedulerFinancialIntentDispatcher:
    def __init__(self, audit_root: Path | None = None) -> None:
        self.audit_root = audit_root or (Path.home()/".companyos_runtime"/"scheduler_financial_dispatcher")
        self.audit_root.mkdir(parents=True, exist_ok=True)

    def dispatch(self, intent: SchedulerFinancialIntent) -> SchedulerFinancialDispatchResult:
        destination = str(intent.destination or "").strip()
        amount_sol = float(intent.amount_sol)
        mode = str(intent.requested_mode or "dry_run").strip().lower()
        action_id = str(intent.action_id or uuid.uuid4())

        if not destination:
            return self._finish(intent, action_id, mode, False, "destination_required")
        if amount_sol <= 0:
            return self._finish(intent, action_id, mode, False, "amount_must_be_positive")
        if mode not in {"dry_run","live"}:
            return self._finish(intent, action_id, mode, False, "unsupported_requested_mode")

        try:
            r = execute_financial_action_from_scheduler({
                "destination": destination,
                "amount_sol": amount_sol,
                "action_id": action_id,
                "source": str(intent.source or "autonomous_scheduler"),
                "requested_mode": mode,
                "confirm_token": str(intent.confirm_token or ""),
                "metadata": intent.metadata or {},
            })
        except Exception as exc:
            return self._finish(intent, action_id, mode, False, f"{type(exc).__name__}:{str(exc)[:300]}")

        out = SchedulerFinancialDispatchResult(
            accepted=bool(r.accepted),
            reason=str(r.reason),
            action_id=action_id,
            requested_mode=mode,
            state=r.state,
            signature=r.signature,
            lifecycle_id=r.lifecycle_id,
            confirmation_status=r.confirmation_status,
        )
        self._write(intent, out)
        return out

    def _finish(self, intent, action_id, mode, accepted, reason):
        out = SchedulerFinancialDispatchResult(
            accepted=accepted, reason=reason, action_id=action_id, requested_mode=mode,
            state=None, signature=None, lifecycle_id=None, confirmation_status=None,
        )
        self._write(intent, out)
        return out

    def _write(self, intent, result):
        now=time.time()
        payload={
            "event_id": str(uuid.uuid4()),
            "created_at_unix": now,
            "intent": {
                "destination": str(intent.destination or ""),
                "amount_sol": float(intent.amount_sol),
                "action_id": result.action_id,
                "source": str(intent.source or "autonomous_scheduler"),
                "requested_mode": result.requested_mode,
                "metadata": intent.metadata or {},
            },
            "result": asdict(result),
        }
        day=time.strftime("%Y-%m-%d", time.localtime(now))
        d=self.audit_root/day
        d.mkdir(parents=True, exist_ok=True)
        p=d/f"{int(now*1000)}_{payload['event_id']}.json"
        tmp=p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        tmp.replace(p)
