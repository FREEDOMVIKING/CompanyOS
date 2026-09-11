from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any
import json
import os
import time

from companyos.runtime_financial_queue import (
    pending_items,
    claim,
    release,
    complete,
)

from companyos.runtime.scheduler_financial_entrypoint import (
    dispatch_scheduler_financial_intent,
)

STATE_ROOT = Path(os.getenv(
    "COMPANYOS_FINANCIAL_WORKER_STATE_ROOT",
    "companyos_runtime/financial_queue_worker"
))
STATE_ROOT.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_ROOT / "status.json"


def _normalize_result(obj: Any) -> dict[str, Any]:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    return {"value": str(obj)}


def _write_status(payload: dict[str, Any]) -> None:
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    os.replace(tmp, STATE_FILE)


def process_one(item) -> dict[str, Any]:
    result = dispatch_scheduler_financial_intent({
        "action_type": item.action_type,
        "destination": item.destination,
        "amount_sol": item.sol,
        "action_id": item.queue_id,
        "source": item.source,
        "requested_mode": os.getenv("COMPANYOS_AUTONOMOUS_FINANCIAL_MODE", "dry_run").strip().lower(),
        "confirm_token": os.getenv("COMPANYOS_LIVE_CONFIRM_TOKEN", "").strip(),
        "metadata": {
            "queue_id": item.queue_id,
            "idempotency_key": item.idempotency_key,
            "queue_worker": True,
        },
    })
    return _normalize_result(result)


def run_once(max_items: int = 10) -> dict[str, Any]:
    started = time.time()
    items = pending_items()[:max_items]

    summary = {
        "started_at": started,
        "finished_at": None,
        "pending_seen": len(items),
        "processed": 0,
        "failed": 0,
        "skipped_claimed": 0,
        "last_error": None,
        "mode": "dry_run",
    }

    for item in items:
        if not claim(item):
            summary["skipped_claimed"] += 1
            continue

        try:
            result = process_one(item)
            complete(item, result)
            summary["processed"] += 1
        except Exception as exc:
            release(item)
            summary["failed"] += 1
            summary["last_error"] = f"{type(exc).__name__}:{str(exc)[:300]}"

    summary["finished_at"] = time.time()
    summary["duration_seconds"] = round(summary["finished_at"] - started, 3)
    _write_status(summary)
    return summary


def load_status() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"status": "never_run"}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception as exc:
        return {"status": "unreadable", "error": type(exc).__name__}
