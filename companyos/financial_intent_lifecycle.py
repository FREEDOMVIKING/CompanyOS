from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional
import json
import os
import time
import uuid

ROOT = Path(os.getenv(
    "COMPANYOS_FINANCIAL_LIFECYCLE_ROOT",
    "companyos_runtime/financial_intent_lifecycle"
))
ROOT.mkdir(parents=True, exist_ok=True)

VALID_STATES = {
    "QUEUED",
    "CLAIMED",
    "EXECUTING",
    "RETRY_WAIT",
    "COMPLETED",
    "FAILED",
}

@dataclass
class FinancialIntentLifecycleRecord:
    lifecycle_id: str
    queue_id: str
    idempotency_key: str
    action_type: str
    destination: str
    sol: float
    state: str
    attempt_count: int
    max_attempts: int
    created_at: float
    updated_at: float
    next_retry_at: Optional[float]
    last_error: Optional[str]
    result: Optional[dict[str, Any]]
    history: list[dict[str, Any]]

class FinancialIntentLifecycleStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ROOT
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, idem: str) -> Path:
        return self.root / f"{idem}.json"

    def load(self, idem: str) -> Optional[FinancialIntentLifecycleRecord]:
        p = self._path(idem)
        if not p.exists():
            return None
        data = json.loads(p.read_text())
        return FinancialIntentLifecycleRecord(**data)

    def ensure_from_queue_item(self, item, max_attempts: int = 5):
        rec = self.load(item.idempotency_key)
        if rec:
            return rec
        now = time.time()
        rec = FinancialIntentLifecycleRecord(
            lifecycle_id=str(uuid.uuid4()),
            queue_id=item.queue_id,
            idempotency_key=item.idempotency_key,
            action_type=item.action_type,
            destination=item.destination,
            sol=float(item.sol),
            state="QUEUED",
            attempt_count=0,
            max_attempts=max_attempts,
            created_at=now,
            updated_at=now,
            next_retry_at=None,
            last_error=None,
            result=None,
            history=[{"state":"QUEUED","at":now,"reason":"queue_item_registered"}],
        )
        self.save(rec)
        return rec

    def transition(self, rec, state: str, *, reason: str = "", error: str | None = None,
                   result: dict[str, Any] | None = None, next_retry_at: float | None = None):
        state = state.upper()
        if state not in VALID_STATES:
            raise ValueError(f"invalid_state:{state}")
        now = time.time()
        rec.state = state
        rec.updated_at = now
        rec.last_error = error
        rec.next_retry_at = next_retry_at
        if result is not None:
            rec.result = result
        rec.history.append({
            "state": state,
            "at": now,
            "reason": reason,
            "error": error,
        })
        self.save(rec)
        return rec

    def save(self, rec) -> None:
        p = self._path(rec.idempotency_key)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(rec), indent=2, sort_keys=True, default=str) + "\n")
        os.replace(tmp, p)

    def list_records(self):
        out = []
        for p in sorted(self.root.glob("*.json")):
            try:
                out.append(FinancialIntentLifecycleRecord(**json.loads(p.read_text())))
            except Exception:
                continue
        return out

    def recover_stale(self, stale_seconds: int = 300):
        now = time.time()
        recovered = 0
        for rec in self.list_records():
            if rec.state not in {"CLAIMED","EXECUTING"}:
                continue
            if now - rec.updated_at < stale_seconds:
                continue
            if rec.attempt_count >= rec.max_attempts:
                self.transition(
                    rec, "FAILED",
                    reason="stale_execution_max_attempts",
                    error="stale_execution_recovered_to_failed",
                )
            else:
                backoff = min(900, 15 * (2 ** max(rec.attempt_count - 1, 0)))
                self.transition(
                    rec, "RETRY_WAIT",
                    reason="stale_execution_recovered",
                    error="stale_execution_recovered",
                    next_retry_at=now + backoff,
                )
            recovered += 1
        return recovered
