from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from companyos.runtime.ceo_financial_intent_producer import (
    produce_ceo_financial_intent,
)


def _root() -> Path:
    p = Path(
        os.getenv(
            "COMPANYOS_CEO_FIN_SCHED_STATE_ROOT",
            "companyos_runtime/ceo_financial_scheduler",
        )
    )
    p.mkdir(parents=True, exist_ok=True)
    return p


def run_scheduler_financial_cycle(
    *,
    cycle_id: str = "",
    financial_intent: Any = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:

    cycle_id = str(cycle_id or f"scheduler-{int(time.time())}")
    metadata = dict(metadata or {})

    # Structured intent may be supplied explicitly or inside scheduler context.
    if financial_intent is None:
        financial_intent = metadata.get("financial_intent")

    # Never infer a payment from ordinary CEO/scheduler prose.
    if financial_intent is None:
        return {
            "accepted": True,
            "queued": False,
            "deduplicated": False,
            "cycle_id": cycle_id,
            "mode": "dry_run",
            "reason": "no_structured_financial_intent",
        }

    digest = hashlib.sha256(cycle_id.encode()).hexdigest()
    marker = _root() / f"{digest}.json"

    if marker.exists():
        return {
            "accepted": True,
            "queued": False,
            "deduplicated": True,
            "cycle_id": cycle_id,
            "mode": "dry_run",
            "reason": "scheduler_cycle_already_processed",
        }

    # Scheduler integration remains pinned to dry-run during validation.
    old = os.environ.get("COMPANYOS_AUTONOMOUS_FINANCIAL_MODE")
    os.environ["COMPANYOS_AUTONOMOUS_FINANCIAL_MODE"] = "dry_run"

    try:
        producer = produce_ceo_financial_intent(financial_intent)

        result = {
            "accepted": bool(producer.accepted),
            "queued": bool(producer.accepted),
            "deduplicated": False,
            "cycle_id": cycle_id,
            "mode": "dry_run",
            "reason": producer.reason,
            "producer_result": {
                "accepted": producer.accepted,
                "reason": producer.reason,
                "action_id": producer.action_id,
                "queue_id": producer.queue_id,
                "destination": producer.destination,
                "amount_sol": producer.amount_sol,
                "source": producer.source,
                "purpose": producer.purpose,
            },
            "created_at": int(time.time()),
        }

        # Only mark the cycle consumed when producer accepted it.
        if producer.accepted:
            tmp = marker.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(result, indent=2, sort_keys=True, default=str) + "\n"
            )
            tmp.replace(marker)

        return result

    finally:
        if old is None:
            os.environ.pop("COMPANYOS_AUTONOMOUS_FINANCIAL_MODE", None)
        else:
            os.environ["COMPANYOS_AUTONOMOUS_FINANCIAL_MODE"] = old
