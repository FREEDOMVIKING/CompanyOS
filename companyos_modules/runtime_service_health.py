"""Bounded health assessment for critical adaptive runtime services."""
from __future__ import annotations

import json
import sys
import time
from typing import Any, Iterable, Mapping

REQUIRED_SERVICES = (
    "adaptive_worker_factory",
    "adaptive_workforce_execution_bridge",
    "autonomous_diagnostics",
    "autonomous_evidence_acquisition",
    "capability_expansion",
    "capability_feedback",
    "capability_request_executor",
    "closed_loop_outcome_evaluator",
)


def _timestamp(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def assess_services(
    records: Mapping[str, Mapping[str, Any]] | Iterable[Mapping[str, Any]],
    now: float | None = None,
    stale_after: float = 90.0,
) -> dict[str, Any]:
    """Return deterministic health facts without starting, stopping, or mutating services."""
    current = time.time() if now is None else float(now)
    if isinstance(records, Mapping):
        indexed = records
    else:
        indexed = {
            str(item.get("name", item.get("service", ""))): item
            for item in records
            if isinstance(item, Mapping)
        }
    services: dict[str, dict[str, Any]] = {}
    unhealthy = []
    for name in REQUIRED_SERVICES:
        item = indexed.get(name, {})
        state = str(item.get("state", item.get("status", "unknown"))).lower()
        heartbeat = _timestamp(item.get("last_heartbeat", item.get("heartbeat")))
        age = None if heartbeat is None else max(0.0, current - heartbeat)
        reason = None
        if state not in {"running", "healthy", "ready"}:
            reason = "not_running"
        elif age is not None and age > stale_after:
            reason = "stale_heartbeat"
        elif heartbeat is None:
            reason = "missing_heartbeat"
        result = {
            "state": state,
            "heartbeat_age_seconds": age,
            "healthy": reason is None,
        }
        if reason:
            result["reason"] = reason
            unhealthy.append(name)
        services[name] = result
    return {
        "healthy": not unhealthy,
        "checked_at": current,
        "stale_after_seconds": stale_after,
        "unhealthy_services": unhealthy,
        "services": services,
    }


def main() -> None:
    payload = json.load(sys.stdin)
    records = payload.get("services", payload) if isinstance(payload, Mapping) else payload
    print(json.dumps(assess_services(records), sort_keys=True))


if __name__ == "__main__":
    main()
