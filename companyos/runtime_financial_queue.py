from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional
import hashlib
import json
import os
import time
import uuid

ROOT = Path(os.getenv("COMPANYOS_FINANCIAL_QUEUE_ROOT", "companyos_runtime/financial_queue"))
PENDING = ROOT / "pending"
RESULTS = ROOT / "results"
CLAIMS = ROOT / "claims"

for p in (PENDING, RESULTS, CLAIMS):
    p.mkdir(parents=True, exist_ok=True)

@dataclass(frozen=True)
class FinancialQueueItem:
    queue_id: str
    idempotency_key: str
    action_type: str
    destination: str
    sol: float
    created_at: float
    source: str = "autonomous_scheduler"

def _safe_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def make_idempotency_key(action_type: str, destination: str, sol: float, source_ref: str = "") -> str:
    raw = f"{action_type}|{destination}|{float(sol):.9f}|{source_ref}"
    return _safe_key(raw)

def enqueue(*, action_type: str, destination: str, sol: float,
            idempotency_key: Optional[str] = None,
            source_ref: str = "") -> FinancialQueueItem:
    if not action_type:
        raise ValueError("action_type_required")
    if not destination:
        raise ValueError("destination_required")
    if float(sol) < 0:
        raise ValueError("negative_amount_rejected")

    idem = idempotency_key or make_idempotency_key(action_type, destination, sol, source_ref)
    result_path = RESULTS / f"{idem}.json"
    pending_path = PENDING / f"{idem}.json"

    if result_path.exists():
        data = json.loads(result_path.read_text())
        q = data.get("request") or {}
        return FinancialQueueItem(**q)

    if pending_path.exists():
        return FinancialQueueItem(**json.loads(pending_path.read_text()))

    item = FinancialQueueItem(
        queue_id=str(uuid.uuid4()),
        idempotency_key=idem,
        action_type=action_type,
        destination=destination,
        sol=float(sol),
        created_at=time.time(),
    )
    tmp = pending_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(item), indent=2, sort_keys=True))
    os.replace(tmp, pending_path)
    return item

def pending_items() -> list[FinancialQueueItem]:
    out = []
    for p in sorted(PENDING.glob("*.json")):
        try:
            out.append(FinancialQueueItem(**json.loads(p.read_text())))
        except Exception:
            continue
    return out

def claim(item: FinancialQueueItem) -> bool:
    claim_path = CLAIMS / f"{item.idempotency_key}.lock"
    try:
        fd = os.open(str(claim_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False

def release(item: FinancialQueueItem) -> None:
    try:
        (CLAIMS / f"{item.idempotency_key}.lock").unlink()
    except FileNotFoundError:
        pass

def complete(item: FinancialQueueItem, result: dict[str, Any]) -> Path:
    payload = {
        "request": asdict(item),
        "result": result,
        "completed_at": time.time(),
    }
    out = RESULTS / f"{item.idempotency_key}.json"
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    os.replace(tmp, out)
    try:
        (PENDING / f"{item.idempotency_key}.json").unlink()
    except FileNotFoundError:
        pass
    release(item)
    return out
