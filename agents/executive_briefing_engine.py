#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "executive_briefing_config.json"
BRIEF = MEMORY / "daily_executive_brief.json"
HEALTH = MEMORY / "executive_briefing_health.json"
AUDIT = MEMORY / "executive_briefing_audit.json"

INTEGRITY = MEMORY / "system_integrity_health.json"
WATCHDOG = MEMORY / "watchdog_health.json"
OPERATIONS = MEMORY / "autonomous_operations_health.json"
PRIORITIES = MEMORY / "executive_priority_rankings.json"
DECISIONS = MEMORY / "ceo_decision_queue.json"
PERFORMANCE = MEMORY / "performance_analytics_report.json"
FORECAST = MEMORY / "business_forecasting_briefing.json"
IMPROVEMENTS = MEMORY / "continuous_improvement_briefing.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)


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


def generate() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    if not config.get("enabled", True):
        result = {"success": False, "status": "executive_briefing_disabled"}
        audit("generate", result)
        return result

    integrity = load_json(INTEGRITY, {})
    watchdog = load_json(WATCHDOG, {})
    operations = load_json(OPERATIONS, {})
    priorities = load_json(PRIORITIES, {}).get("rankings", {}).get("priorities", [])
    decisions = load_json(DECISIONS, {}).get("decisions", [])
    pending_decisions = [d for d in decisions if d.get("status") == "pending"]
    performance = load_json(PERFORMANCE, {}).get("report", {})
    forecast = load_json(FORECAST, {}).get("briefing", {})
    improvements = load_json(IMPROVEMENTS, {}).get("briefing", {})

    attention = []
    if integrity and integrity.get("healthy") is not True:
        attention.append("System integrity needs attention.")
    if watchdog and watchdog.get("healthy") is not True:
        attention.append("Watchdog health needs attention.")
    if operations and operations.get("healthy") is not True:
        attention.append("Autonomous operations reported an issue.")
    if pending_decisions:
        attention.append(f"{len(pending_decisions)} CEO decision(s) are pending review.")
    critical = [p for p in priorities if p.get("priority_band") == "critical"]
    if critical:
        attention.append(f"{len(critical)} critical priority item(s) require attention.")
    if not attention:
        attention.append("No critical operating issue detected.")

    brief = {
        "generated_at": now(),
        "headline": "CompanyOS Autonomous Executive Brief",
        "system_health": {
            "integrity": integrity,
            "watchdog": watchdog,
            "autonomous_operations": operations,
        },
        "top_priorities": priorities[:5],
        "pending_decisions": pending_decisions[:5],
        "performance_summary": {
            "headline": performance.get("headline"),
            "health_score": performance.get("health_score"),
            "attention_items": performance.get("attention_items", []),
        },
        "forecast_summary": {
            "headline": forecast.get("headline"),
            "confidence_percent": forecast.get("confidence_percent"),
            "scenarios": forecast.get("scenarios", {}),
            "top_risks": forecast.get("top_risks", []),
            "top_opportunities": forecast.get("top_opportunities", []),
        },
        "improvement_summary": {
            "headline": improvements.get("headline"),
            "top_recommendations": improvements.get("top_recommendations", [])[:5],
        },
        "attention_items": attention,
        "recommended_next_actions": [
            item.get("title") for item in priorities[:5] if item.get("title")
        ],
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    save_json(BRIEF, brief)
    save_json(HEALTH, {
        "healthy": True,
        "last_generated_at": now(),
        "priority_count": len(priorities),
        "pending_decision_count": len(pending_decisions),
        "attention_count": len(attention),
        "last_error": None,
    })

    result = {"success": True, "status": "executive_brief_generated", "brief": brief}
    audit("generate", result)
    return result


def show() -> dict[str, Any]:
    data = load_json(BRIEF, {})
    result = {"success": bool(data), "status": "executive_brief", "brief": data}
    audit("show", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "executive_briefing_status",
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
        if action == "generate":
            return print_result(generate())
        if action == "show":
            return print_result(show())
        if action == "status":
            return print_result(status())
        return print_result({
            "success": False,
            "status": "unknown_brief_action",
            "action": action,
            "allowed": ["generate", "show", "status"],
        })
    except Exception as exc:
        result = {
            "success": False,
            "status": "executive_briefing_error",
            "error": str(exc),
        }
        save_json(HEALTH, {
            "healthy": False,
            "last_checked_at": now(),
            "last_error": str(exc),
        })
        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
