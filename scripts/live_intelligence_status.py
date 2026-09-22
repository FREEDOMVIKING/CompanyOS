#!/usr/bin/env python3
"""Read-only health snapshot for runtime services.

Each service may publish JSON to COMPANYOS_HEALTH_DIR/<service>.json with a
status of running, degraded, or stopped and an optional heartbeat timestamp.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SERVICES = (
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
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def inspect_service(directory: Path, service: str, now: float, max_age: float) -> dict[str, Any]:
    path = directory / f"{service}.json"
    result: dict[str, Any] = {"service": service, "status": "unknown", "source": str(path)}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        result.update(status="unhealthy", reason="missing_health_record")
        return result
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        result.update(status="unhealthy", reason="invalid_health_record", detail=str(exc))
        return result
    if not isinstance(payload, dict):
        result.update(status="unhealthy", reason="health_record_is_not_an_object")
        return result

    state = str(payload.get("status", "")).lower()
    heartbeat = _timestamp(payload.get("heartbeat_at", payload.get("timestamp")))
    result["reported_status"] = state or "missing"
    if heartbeat is not None:
        result["heartbeat_age_seconds"] = round(max(0.0, now - heartbeat), 3)
    if state not in {"running", "degraded", "stopped"}:
        result.update(status="unhealthy", reason="invalid_status")
    elif heartbeat is None:
        result.update(status="unhealthy", reason="missing_heartbeat")
    elif now - heartbeat > max_age:
        result.update(status="unhealthy", reason="stale_heartbeat")
    elif state == "stopped":
        result.update(status="unhealthy", reason="reported_stopped")
    else:
        result["status"] = state
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--health-dir",
        default=os.environ.get("COMPANYOS_HEALTH_DIR", "/tmp/companyos/health"),
    )
    parser.add_argument("--max-age", type=float, default=120.0)
    args = parser.parse_args(argv)
    if args.max_age <= 0:
        parser.error("--max-age must be positive")

    now = time.time()
    services = [inspect_service(Path(args.health_dir), name, now, args.max_age) for name in SERVICES]
    summary = {
        "healthy": sum(item["status"] == "running" for item in services),
        "degraded": sum(item["status"] == "degraded" for item in services),
        "unhealthy": sum(item["status"] == "unhealthy" for item in services),
        "unknown": sum(item["status"] == "unknown" for item in services),
    }
    print(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "summary": summary, "services": services}, sort_keys=True))
    return 0 if summary["unhealthy"] == 0 and summary["unknown"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
