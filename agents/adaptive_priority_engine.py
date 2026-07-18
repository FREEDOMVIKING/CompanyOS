#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "adaptive_priority_config.json"
ACTION_QUEUE = MEM / "action_queue_report.json"
DISPATCH = MEM / "action_dispatcher_report.json"
FEEDBACK = MEM / "dispatcher_feedback_report.json"

STATE = MEM / "adaptive_priority_state.json"
REPORT = MEM / "adaptive_priority_report.json"
HEALTH = MEM / "adaptive_priority_health.json"

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))

def run() -> dict[str, Any]:
    cfg = load(CFG, {})
    queue = load(ACTION_QUEUE, {}).get("queue", [])
    dispatch = load(DISPATCH, {})
    feedback = load(FEEDBACK, {})

    success_bonus = int(cfg.get("success_bonus", 10))
    failure_penalty = int(cfg.get("failure_penalty", 20))
    blocked_penalty = int(cfg.get("blocked_penalty", 5))
    maximum_adjustment = int(cfg.get("maximum_adjustment", 30))
    minimum_priority = int(cfg.get("minimum_priority", 1))
    maximum_priority = int(cfg.get("maximum_priority", 100))

    outcomes = {}

    for item in dispatch.get("results", []):
        action = item.get("action")
        if not action:
            continue
        if item.get("success"):
            outcomes.setdefault(action, {"success": 0, "failure": 0, "blocked": 0})
            outcomes[action]["success"] += 1
        else:
            outcomes.setdefault(action, {"success": 0, "failure": 0, "blocked": 0})
            outcomes[action]["failure"] += 1

    for item in dispatch.get("blocked", []):
        action = item.get("action")
        if not action:
            continue
        outcomes.setdefault(action, {"success": 0, "failure": 0, "blocked": 0})
        outcomes[action]["blocked"] += 1

    repeated_failures = feedback.get("repeated_failures", {})

    adjusted = []

    for item in queue:
        action = item.get("action")
        base = int(item.get("priority", 50))
        stats = outcomes.get(action, {"success": 0, "failure": 0, "blocked": 0})

        adjustment = (
            stats["success"] * success_bonus
            - stats["failure"] * failure_penalty
            - stats["blocked"] * blocked_penalty
        )

        if int(repeated_failures.get(action, 0)) > 0:
            adjustment -= failure_penalty

        adjustment = clamp(
            adjustment,
            -maximum_adjustment,
            maximum_adjustment
        )

        adaptive = clamp(
            base + adjustment,
            minimum_priority,
            maximum_priority
        )

        adjusted.append({
            "action": action,
            "base_priority": base,
            "adjustment": adjustment,
            "adaptive_priority": adaptive,
            "reason": item.get("reason"),
            "outcomes": stats
        })

    adjusted.sort(
        key=lambda x: x["adaptive_priority"],
        reverse=True
    )

    report = {
        "generated_at": now(),
        "adaptive_priorities": adjusted,
        "top_action": adjusted[0]["action"] if adjusted else None,
        "top_priority": adjusted[0]["adaptive_priority"] if adjusted else None,
        "automatic_external_write": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_updated_at": now(),
        "action_count": len(adjusted),
        "top_action": report["top_action"],
        "top_priority": report["top_priority"]
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "action_count": len(adjusted)
    })

    return {
        "success": True,
        "status": "adaptive_prioritization_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "adaptive_priority_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = run()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["run", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
