#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "executive_priority_config.json"
RANKINGS = MEMORY / "executive_priority_rankings.json"
BRIEFING = MEMORY / "executive_priority_briefing.json"
HEALTH = MEMORY / "executive_priority_health.json"
AUDIT = MEMORY / "executive_priority_audit.json"

DISCOVERY = MEMORY / "opportunity_discovery_results.json"
EXECUTIVE = MEMORY / "ai_executive_briefing.json"
TASKS = MEMORY / "product_execution_tasks.json"
FOLLOWUPS = MEMORY / "sales_followups.json"
PROJECTS = MEMORY / "project_registry.json"
INVOICES = MEMORY / "invoice_registry.json"


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


def make_id(seed: str) -> str:
    digest = hashlib.sha256(
        f"{seed}:{now()}".encode("utf-8")
    ).hexdigest()[:12]
    return f"priority-{digest}"


def number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def calculate_score(
    urgency: float,
    profitability: float,
    risk_reduction: float,
    execution_ease: float,
    evidence: float,
    weights: dict[str, Any],
) -> float:
    score = (
        urgency * number(weights.get("urgency"), 0.30)
        + profitability * number(weights.get("profitability"), 0.30)
        + risk_reduction * number(weights.get("risk_reduction"), 0.20)
        + execution_ease * number(weights.get("execution_ease"), 0.10)
        + evidence * number(weights.get("evidence"), 0.10)
    )
    return round(clamp(score), 2)


def priority_band(score: float) -> str:
    if score >= 85:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 55:
        return "medium"
    return "low"


def from_discovery(
    opportunity: dict[str, Any],
    weights: dict[str, Any],
) -> dict[str, Any]:
    profitability = number(opportunity.get("revenue_potential"), 50)
    ease = number(opportunity.get("ease_of_execution"), 50)
    evidence = number(opportunity.get("evidence_strength"), 50)
    confidence = number(opportunity.get("confidence"), 50)

    category = str(opportunity.get("category") or "general")
    urgency = 70 if category in {"cash_recovery", "sales"} else 55
    risk_reduction = 85 if category == "cash_recovery" else confidence

    score = calculate_score(
        urgency,
        profitability,
        risk_reduction,
        ease,
        evidence,
        weights,
    )

    return {
        "id": make_id(str(opportunity.get("id"))),
        "source_type": "opportunity",
        "source_id": opportunity.get("id"),
        "title": opportunity.get("title"),
        "category": category,
        "description": opportunity.get("description"),
        "urgency": urgency,
        "profitability": profitability,
        "risk_reduction": risk_reduction,
        "execution_ease": ease,
        "evidence": evidence,
        "estimated_value": number(opportunity.get("estimated_value"), 0),
        "score": score,
        "priority_band": priority_band(score),
        "recommended_action": "owner_review",
        "owner_approval_required": True,
        "external_action_authorized": False,
        "created_at": now(),
    }


def from_task(
    task: dict[str, Any],
    weights: dict[str, Any],
) -> dict[str, Any]:
    name = str(task.get("name") or "Internal task")
    urgency = number(task.get("priority"), 60)
    profitability = 45
    risk_reduction = 55
    ease = 75
    evidence = 80

    if "invoice" in name.lower() or "payment" in name.lower():
        profitability = 80
        urgency = 80
        risk_reduction = 75

    score = calculate_score(
        urgency,
        profitability,
        risk_reduction,
        ease,
        evidence,
        weights,
    )

    return {
        "id": make_id(str(task.get("id"))),
        "source_type": "internal_task",
        "source_id": task.get("id"),
        "title": name,
        "category": "operations",
        "description": task.get("description"),
        "urgency": urgency,
        "profitability": profitability,
        "risk_reduction": risk_reduction,
        "execution_ease": ease,
        "evidence": evidence,
        "estimated_value": 0.0,
        "score": score,
        "priority_band": priority_band(score),
        "recommended_action": "internal_execution_review",
        "owner_approval_required": False,
        "external_action_authorized": False,
        "created_at": now(),
    }


def generate() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "executive_priority_engine_disabled",
        }
        audit("generate", result)
        return result

    weights = config.get("weights", {})

    opportunities = load_json(
        DISCOVERY,
        {},
    ).get("results", {}).get("opportunities", [])

    tasks = [
        item for item in load_json(TASKS, {}).get("tasks", [])
        if item.get("status") == "pending"
    ]

    followups = [
        item for item in load_json(FOLLOWUPS, {}).get("followups", [])
        if item.get("status") == "pending"
    ]

    projects = [
        item for item in load_json(PROJECTS, {}).get("projects", [])
        if item.get("status") in {"planning", "waiting", "in_progress"}
    ]

    invoices = [
        item for item in load_json(INVOICES, {}).get("invoices", [])
        if number(item.get("balance_due"), 0) > 0
        and item.get("status") != "void"
    ]

    priorities: list[dict[str, Any]] = []

    priorities.extend(
        from_discovery(item, weights)
        for item in opportunities
    )

    priorities.extend(
        from_task(item, weights)
        for item in tasks
    )

    for followup in followups:
        score = calculate_score(
            82, 65, 70, 78, 85, weights
        )
        priorities.append({
            "id": make_id(str(followup.get("id"))),
            "source_type": "followup",
            "source_id": followup.get("id"),
            "title": f"Review follow-up: {followup.get('customer_name')}",
            "category": "sales",
            "description": followup.get("note"),
            "urgency": 82,
            "profitability": 65,
            "risk_reduction": 70,
            "execution_ease": 78,
            "evidence": 85,
            "estimated_value": 0.0,
            "score": score,
            "priority_band": priority_band(score),
            "recommended_action": "owner_review",
            "owner_approval_required": True,
            "external_action_authorized": False,
            "created_at": now(),
        })

    for invoice in invoices:
        value = number(invoice.get("balance_due"), 0)
        score = calculate_score(
            95, 95, 90, 65, 95, weights
        )
        priorities.append({
            "id": make_id(str(invoice.get("id"))),
            "source_type": "invoice",
            "source_id": invoice.get("id"),
            "title": f"Review receivable: {invoice.get('customer_name')}",
            "category": "finance",
            "description": (
                f"Invoice has ${value:,.2f} outstanding."
            ),
            "urgency": 95,
            "profitability": 95,
            "risk_reduction": 90,
            "execution_ease": 65,
            "evidence": 95,
            "estimated_value": value,
            "score": score,
            "priority_band": priority_band(score),
            "recommended_action": "owner_review",
            "owner_approval_required": True,
            "external_action_authorized": False,
            "created_at": now(),
        })

    for project in projects:
        progress = number(project.get("progress_percent"), 0)
        if progress >= 75:
            continue

        urgency = 75 if project.get("status") == "waiting" else 62
        score = calculate_score(
            urgency, 55, 72, 70, 80, weights
        )

        priorities.append({
            "id": make_id(str(project.get("id"))),
            "source_type": "project",
            "source_id": project.get("id"),
            "title": f"Advance project: {project.get('project_name')}",
            "category": "operations",
            "description": (
                f"Project is {progress:.0f}% complete and currently "
                f"{project.get('status')}."
            ),
            "urgency": urgency,
            "profitability": 55,
            "risk_reduction": 72,
            "execution_ease": 70,
            "evidence": 80,
            "estimated_value": number(project.get("amount"), 0),
            "score": score,
            "priority_band": priority_band(score),
            "recommended_action": "internal_execution_review",
            "owner_approval_required": False,
            "external_action_authorized": False,
            "created_at": now(),
        })

    priorities.sort(
        key=lambda item: (
            number(item.get("score"), 0),
            number(item.get("estimated_value"), 0),
        ),
        reverse=True,
    )

    maximum = int(config.get("maximum_priorities", 15))
    priorities = priorities[:maximum]

    for index, item in enumerate(priorities, start=1):
        item["rank"] = index

    total_estimated_value = round(
        sum(number(item.get("estimated_value"), 0) for item in priorities),
        2,
    )

    rankings = {
        "generated_at": now(),
        "count": len(priorities),
        "total_estimated_value": total_estimated_value,
        "priorities": priorities,
        "automatic_task_execution": False,
        "automatic_customer_contact": False,
        "automatic_external_execution": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    save_json(
        RANKINGS,
        {
            "schema_version": 1,
            "rankings": rankings,
            "last_updated_at": now(),
        },
    )

    top = priorities[:5]
    briefing = {
        "generated_at": now(),
        "headline": (
            f"{len(priorities)} priorities ranked; "
            f"{len(top)} selected for executive focus."
        ),
        "top_priorities": top,
        "critical_count": sum(
            1 for item in priorities
            if item.get("priority_band") == "critical"
        ),
        "high_count": sum(
            1 for item in priorities
            if item.get("priority_band") == "high"
        ),
        "medium_count": sum(
            1 for item in priorities
            if item.get("priority_band") == "medium"
        ),
        "total_estimated_value": total_estimated_value,
        "recommended_focus_order": [
            {
                "rank": item["rank"],
                "title": item["title"],
                "category": item["category"],
                "score": item["score"],
                "owner_approval_required": item["owner_approval_required"],
            }
            for item in top
        ],
        "automatic_external_execution": False,
        "automatic_spending": False,
    }

    save_json(
        BRIEFING,
        {
            "schema_version": 1,
            "briefing": briefing,
            "last_updated_at": now(),
        },
    )

    save_json(
        HEALTH,
        {
            "healthy": True,
            "last_generated_at": now(),
            "priority_count": len(priorities),
            "critical_count": briefing["critical_count"],
            "high_count": briefing["high_count"],
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "executive_priorities_ranked",
        "rankings": rankings,
        "briefing": briefing,
    }

    audit("generate", result)
    return result


def show() -> dict[str, Any]:
    rankings = load_json(RANKINGS, {}).get("rankings")
    result = {
        "success": bool(rankings),
        "status": "executive_priority_rankings",
        "rankings": rankings,
    }
    audit("show", result)
    return result


def briefing() -> dict[str, Any]:
    data = load_json(BRIEFING, {}).get("briefing")
    result = {
        "success": bool(data),
        "status": "executive_priority_briefing",
        "briefing": data,
    }
    audit("briefing", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    health = load_json(HEALTH, {})
    result = {
        "success": True,
        "status": "executive_priority_status",
        "enabled": config.get("enabled", False),
        "automatic_internal_ranking": config.get(
            "automatic_internal_ranking", False
        ),
        "automatic_internal_briefing": config.get(
            "automatic_internal_briefing", False
        ),
        "automatic_task_execution": config.get(
            "automatic_task_execution", False
        ),
        "automatic_customer_contact": config.get(
            "automatic_customer_contact", False
        ),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_publication": config.get(
            "automatic_publication", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "health": health,
    }
    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "rank":
            return print_result(generate())

        if action == "show":
            return print_result(show())

        if action == "briefing":
            return print_result(briefing())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_priority_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "executive_priority_error",
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
