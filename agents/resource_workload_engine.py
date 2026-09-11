#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "resource_workload_config.json"
STATE = MEMORY / "resource_workload_state.json"
HEALTH = MEMORY / "resource_workload_health.json"
AUDIT = MEMORY / "resource_workload_audit.json"

OPS_CONFIG = MEMORY / "autonomous_operations_config.json"
OPS_STATE = MEMORY / "autonomous_operations_state.json"
PRIORITIES = MEMORY / "executive_priority_rankings.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    tmp.replace(path)


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT, [])
    if not isinstance(records, list):
        records = []
    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })
    save_json(AUDIT, records[-1000:])


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def optimize() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {"success": False, "status": "resource_workload_disabled"}
        audit("optimize", result)
        return result

    ops_config = load_json(OPS_CONFIG, {})
    ops_state = load_json(OPS_STATE, {})
    priorities = load_json(
        PRIORITIES,
        {},
    ).get("rankings", {}).get("priorities", [])

    jobs = ops_config.get("jobs", [])
    job_state = ops_state.get("jobs", {})

    min_interval = int(config.get("minimum_interval_seconds", 600))
    max_interval = int(config.get("maximum_interval_seconds", 43200))
    fail_threshold = int(config.get("high_failure_threshold", 3))
    duration_threshold = float(
        config.get("high_duration_threshold_seconds", 60)
    )
    freq_floor = int(
        config.get("high_frequency_floor_seconds", 900)
    )

    critical_count = sum(
        1 for item in priorities
        if item.get("priority_band") == "critical"
    )
    high_count = sum(
        1 for item in priorities
        if item.get("priority_band") == "high"
    )

    changes = []
    workload = []

    for job in jobs:
        job_id = str(job.get("id"))
        if not job_id:
            continue

        current = int(job.get("interval_seconds", 3600))
        state = job_state.get(job_id, {})

        failure_count = int(state.get("failure_count", 0))
        duration = float(state.get("last_duration_seconds") or 0.0)
        last_success = state.get("last_success")

        score = 50
        reasons = []

        if failure_count >= fail_threshold or last_success is False:
            score -= 25
            reasons.append("recent_failures")

        if duration >= duration_threshold:
            score -= 15
            reasons.append("long_runtime")

        if critical_count > 0 and job_id in {
            "priority-ranking",
            "decision-preparation",
            "autonomous-orchestrator",
            "exception-recovery",
        }:
            score += 25
            reasons.append("critical_business_pressure")

        if high_count > 0 and job_id in {
            "opportunity-discovery",
            "performance-analytics",
            "business-forecast",
        }:
            score += 10
            reasons.append("high_priority_pressure")

        score = max(0, min(100, score))

        new_interval = current

        if "recent_failures" in reasons or "long_runtime" in reasons:
            new_interval = clamp(
                max(current * 2, freq_floor),
                min_interval,
                max_interval,
            )
        elif score >= 75:
            new_interval = clamp(
                max(min_interval, current // 2),
                min_interval,
                max_interval,
            )
        elif score <= 35:
            new_interval = clamp(
                current * 2,
                min_interval,
                max_interval,
            )

        workload.append({
            "job_id": job_id,
            "score": score,
            "current_interval_seconds": current,
            "recommended_interval_seconds": new_interval,
            "failure_count": failure_count,
            "last_duration_seconds": duration,
            "reasons": reasons,
        })

        if (
            config.get("automatic_scheduler_tuning", True)
            and new_interval != current
        ):
            job["interval_seconds"] = new_interval
            changes.append({
                "job_id": job_id,
                "old_interval_seconds": current,
                "new_interval_seconds": new_interval,
                "reasons": reasons,
            })

    workload.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    if changes:
        save_json(OPS_CONFIG, ops_config)

    state = {
        "generated_at": now(),
        "critical_priority_count": critical_count,
        "high_priority_count": high_count,
        "job_count": len(workload),
        "changes_applied": len(changes),
        "changes": changes,
        "workload": workload,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False,
    }
    save_json(STATE, state)

    save_json(
        HEALTH,
        {
            "healthy": True,
            "last_optimized_at": now(),
            "job_count": len(workload),
            "changes_applied": len(changes),
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "resource_workload_optimization_complete",
        "state": state,
    }
    audit("optimize", result)
    return result


def show() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "resource_workload_state",
        "state": load_json(STATE, {}),
    }
    audit("show", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "resource_workload_status",
        "config": load_json(CONFIG, {}),
        "health": load_json(HEALTH, {}),
    }
    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "optimize":
            return print_result(optimize())
        if action == "show":
            return print_result(show())
        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_resource_action",
            "action": action,
            "allowed": ["optimize", "show", "status"],
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "resource_workload_error",
            "error": str(exc),
        }
        save_json(
            HEALTH,
            {
                "healthy": False,
                "last_checked_at": now(),
                "last_error": str(exc),
            },
        )
        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
