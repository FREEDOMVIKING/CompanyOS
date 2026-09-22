"""Read-only runtime health report for critical CompanyOS workers."""
from __future__ import annotations

import argparse
import json
import os
import re
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
_SAFE_NAME = re.compile(r"^[a-z0-9_]+$")


def _epoch(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return None
    return None


def inspect_service(root: Path, name: str, now: float, max_age: float) -> dict[str, Any]:
    if not _SAFE_NAME.fullmatch(name):
        return {"name": name, "state": "invalid_name", "healthy": False}
    path = root / f"{name}.json"
    if not path.is_file():
        return {"name": name, "state": "missing_heartbeat", "healthy": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"name": name, "state": "invalid_heartbeat", "healthy": False,
                "detail": type(exc).__name__}
    if not isinstance(payload, dict):
        return {"name": name, "state": "invalid_heartbeat", "healthy": False,
                "detail": "heartbeat must be an object"}
    stamp = next((_epoch(payload.get(key)) for key in
                  ("last_seen", "timestamp", "updated_at") if payload.get(key) is not None), None)
    if stamp is None:
        return {"name": name, "state": "missing_timestamp", "healthy": False}
    age = max(0.0, now - stamp)
    declared = str(payload.get("status", "running")).lower()
    healthy = declared in {"running", "ready", "healthy"} and age <= max_age
    state = "running" if healthy else ("stale_heartbeat" if age > max_age else "not_running")
    return {"name": name, "state": state, "healthy": healthy,
            "heartbeat_age_seconds": round(age, 3), "reported_status": declared}


def report(root: Path, max_age: float) -> dict[str, Any]:
    now = time.time()
    services = [inspect_service(root, name, now, max_age) for name in SERVICES]
    healthy = sum(item["healthy"] for item in services)
    return {"heartbeat_dir": str(root), "max_age_seconds": max_age,
            "ok": healthy == len(services), "healthy": healthy,
            "total": len(services), "services": services}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--heartbeat-dir", type=Path,
                        default=Path(os.environ.get("COMPANYOS_HEARTBEAT_DIR", "/tmp/companyos/heartbeats")))
    parser.add_argument("--max-age", type=float, default=120.0)
    args = parser.parse_args()
    if args.max_age <= 0:
        parser.error("--max-age must be positive")
    print(json.dumps(report(args.heartbeat_dir, args.max_age), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
