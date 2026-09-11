from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional
import hashlib
import json
import re
import time

from companyos.scheduler_financial_queue_bridge import queue_scheduler_financial_intent

AUDIT_ROOT = Path("companyos_runtime/ceo_financial_intent_producer")
AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
_SOL_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

@dataclass(frozen=True)
class ProducerResult:
    accepted: bool
    reason: str
    action_id: str
    queue_id: Optional[str]
    destination: str
    amount_sol: float
    source: str
    purpose: str
    created_at: float

def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)

def _audit(result: ProducerResult) -> None:
    day = time.strftime("%Y-%m-%d")
    d = AUDIT_ROOT / day
    d.mkdir(parents=True, exist_ok=True)
    payload = {"result": asdict(result)}
    raw = json.dumps(payload, sort_keys=True, default=str).encode()
    p = d / (hashlib.sha256(raw).hexdigest()[:20] + ".json")
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    tmp.replace(p)

def _finish(**kwargs) -> ProducerResult:
    r = ProducerResult(created_at=time.time(), **kwargs)
    _audit(r)
    return r

def produce_ceo_financial_intent(intent: Any) -> ProducerResult:
    action_type = str(_get(intent, "action_type", "") or "").strip().lower()
    destination = str(_get(intent, "destination", "") or "").strip()
    source = str(_get(intent, "source", "autonomous_ceo") or "autonomous_ceo").strip()
    purpose = str(_get(intent, "purpose", "") or "").strip()
    action_id = str(_get(intent, "action_id", "") or "").strip()
    metadata = _get(intent, "metadata", {}) or {}

    try:
        amount_sol = float(_get(intent, "amount_sol", _get(intent, "sol", _get(intent, "amount", 0.0))))
    except Exception:
        return _finish(
            accepted=False, reason="invalid_amount", action_id=action_id, queue_id=None,
            destination=destination, amount_sol=0.0, source=source, purpose=purpose
        )

    common = dict(
        action_id=action_id, queue_id=None, destination=destination,
        amount_sol=amount_sol, source=source, purpose=purpose
    )

    if action_type != "sol_transfer":
        return _finish(accepted=False, reason="unsupported_action_type", **common)
    if not action_id:
        return _finish(accepted=False, reason="action_id_required", **common)
    if not destination or not _SOL_RE.match(destination):
        return _finish(accepted=False, reason="invalid_destination", **common)
    if amount_sol <= 0:
        return _finish(accepted=False, reason="amount_must_be_positive", **common)
    if not purpose:
        return _finish(accepted=False, reason="purpose_required", **common)

    queue_payload = {
        "action_type": "sol_transfer",
        "destination": destination,
        "sol": amount_sol,
        "amount_sol": amount_sol,
        "source": source,
        "source_ref": action_id,
        "action_id": action_id,
        "purpose": purpose,
        "metadata": {
            "producer": "ceo_financial_intent_producer",
            "purpose": purpose,
            "action_id": action_id,
            **(metadata if isinstance(metadata, dict) else {}),
        },
    }

    try:
        q = queue_scheduler_financial_intent(queue_payload)
    except Exception as exc:
        return _finish(
            accepted=False,
            reason=f"queue_error:{type(exc).__name__}:{str(exc)[:180]}",
            **common
        )

    queue_id = str(_get(q, "queue_id", _get(q, "id", _get(q, "action_id", ""))) or "") or None
    return _finish(
        accepted=True, reason="queued", action_id=action_id, queue_id=queue_id,
        destination=destination, amount_sol=amount_sol, source=source, purpose=purpose
    )
