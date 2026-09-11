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

CONFIG = MEMORY / "continuous_improvement_config.json"
FINDINGS = MEMORY / "continuous_improvement_findings.json"
BACKLOG = MEMORY / "continuous_improvement_backlog.json"
BRIEFING = MEMORY / "continuous_improvement_briefing.json"
HEALTH = MEMORY / "continuous_improvement_health.json"
AUDIT = MEMORY / "continuous_improvement_audit.json"

PRIORITIES = MEMORY / "executive_priority_rankings.json"
DECISIONS = MEMORY / "ceo_decision_queue.json"
PLANS = MEMORY / "decision_execution_plans.json"
TASKS = MEMORY / "product_execution_tasks.json"
PROJECTS = MEMORY / "project_registry.json"
INVOICES = MEMORY / "invoice_registry.json"
AUTOMATION = MEMORY / "automation_registry.json"


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


def make_id(seed: str) -> str:
    digest = hashlib.sha256(
        f"{seed}:{now()}".encode("utf-8")
    ).hexdigest()[:12]
    return f"improvement-{digest}"


def number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


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


def score(impact: float, urgency: float, ease: float, evidence: float) -> float:
    return round(
        max(
            0.0,
            min(
                100.0,
                impact * 0.35
                + urgency * 0.30
                + ease * 0.15
                + evidence * 0.20,
            ),
        ),
        2,
    )


def band(value: float) -> str:
    if value >= 85:
        return "critical"
    if value >= 70:
        return "high"
    if value >= 55:
        return "medium"
    return "low"


def finding(
    title: str,
    category: str,
    description: str,
    recommendation: str,
    impact: float,
    urgency: float,
    ease: float,
    evidence: float,
    source: str,
) -> dict[str, Any]:
    value = score(impact, urgency, ease, evidence)

    return {
        "id": make_id(f"{category}:{title}"),
        "title": title,
        "category": category,
        "description": description,
        "recommendation": recommendation,
        "impact": impact,
        "urgency": urgency,
        "ease": ease,
        "evidence": evidence,
        "score": value,
        "priority_band": band(value),
        "source": source,
        "owner_approval_required": True,
        "automatic_code_changes": False,
        "automatic_execution": False,
        "external_action_authorized": False,
        "created_at": now(),
    }


def analyze() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "continuous_improvement_engine_disabled",
        }
        audit("analyze", result)
        return result

    priorities = load_json(
        PRIORITIES,
        {},
    ).get("rankings", {}).get("priorities", [])

    decisions = load_json(DECISIONS, {}).get("decisions", [])
    plans = load_json(PLANS, {}).get("plans", [])
    tasks = load_json(TASKS, {}).get("tasks", [])
    projects = load_json(PROJECTS, {}).get("projects", [])
    invoices = load_json(INVOICES, {}).get("invoices", [])
    automations = load_json(AUTOMATION, {}).get("automations", [])

    findings: list[dict[str, Any]] = []

    pending_tasks = [
        item for item in tasks
        if item.get("status") == "pending"
    ]

    if len(pending_tasks) >= 5:
        findings.append(
            finding(
                "Reduce pending task backlog",
                "operations",
                f"{len(pending_tasks)} internal tasks are pending.",
                "Review, group, and sequence pending internal tasks by business impact.",
                82,
                78,
                72,
                90,
                "product_execution_tasks",
            )
        )

    pending_decisions = [
        item for item in decisions
        if item.get("status") == "pending"
    ]

    if pending_decisions:
        findings.append(
            finding(
                "Clear pending CEO decisions",
                "governance",
                f"{len(pending_decisions)} CEO decisions are waiting for owner review.",
                "Review the highest-scoring pending decisions first.",
                80,
                86,
                88,
                95,
                "ceo_decision_queue",
            )
        )

    ready_plans = [
        item for item in plans
        if item.get("status") == "ready"
    ]

    if ready_plans:
        findings.append(
            finding(
                "Convert approved plans into internal tasks",
                "execution",
                f"{len(ready_plans)} decision execution plans are ready.",
                "Create internal tasks from ready plans without enabling automatic execution.",
                76,
                72,
                90,
                92,
                "decision_execution_plans",
            )
        )

    stalled_projects = [
        item for item in projects
        if item.get("status") in {"waiting", "blocked"}
    ]

    if stalled_projects:
        findings.append(
            finding(
                "Resolve stalled projects",
                "project_delivery",
                f"{len(stalled_projects)} projects are waiting or blocked.",
                "Identify the main dependency for each stalled project and prepare a recovery step.",
                88,
                90,
                65,
                90,
                "project_registry",
            )
        )

    receivables = [
        item for item in invoices
        if number(item.get("balance_due"), 0) > 0
        and item.get("status") != "void"
    ]

    receivable_value = round(
        sum(number(item.get("balance_due"), 0) for item in receivables),
        2,
    )

    if receivables:
        findings.append(
            finding(
                "Improve receivable recovery process",
                "finance",
                f"{len(receivables)} invoices have ${receivable_value:,.2f} outstanding.",
                "Prioritize owner-reviewed follow-up preparation for the largest balances.",
                95,
                95,
                70,
                98,
                "invoice_registry",
            )
        )

    critical_priorities = [
        item for item in priorities
        if item.get("priority_band") == "critical"
    ]

    if critical_priorities:
        findings.append(
            finding(
                "Shorten critical-priority response time",
                "strategy",
                f"{len(critical_priorities)} critical priorities are currently ranked.",
                "Review critical priorities before lower-value operational work.",
                92,
                96,
                85,
                96,
                "executive_priority_rankings",
            )
        )

    if not automations:
        findings.append(
            finding(
                "Establish internal review automations",
                "automation",
                "No automation records were found.",
                "Create internal-only review schedules for priorities, decisions, and operational health.",
                68,
                58,
                75,
                70,
                "automation_registry",
            )
        )

    if not findings:
        findings.append(
            finding(
                "Maintain current operating controls",
                "governance",
                "No major internal process weakness was detected.",
                "Continue periodic internal review and preserve owner approval controls.",
                55,
                50,
                90,
                75,
                "system_review",
            )
        )

    findings.sort(
        key=lambda item: number(item.get("score"), 0),
        reverse=True,
    )

    maximum = int(config.get("maximum_recommendations", 20))
    findings = findings[:maximum]

    for index, item in enumerate(findings, start=1):
        item["rank"] = index

    save_json(
        FINDINGS,
        {
            "schema_version": 1,
            "generated_at": now(),
            "count": len(findings),
            "findings": findings,
            "automatic_code_changes": False,
            "automatic_execution": False,
            "external_action_authorized": False,
        },
    )

    backlog = load_json(
        BACKLOG,
        {
            "schema_version": 1,
            "items": [],
            "statistics": {},
        },
    )

    existing = {
        (
            str(item.get("title")),
            str(item.get("status")),
        )
        for item in backlog.get("items", [])
        if item.get("status") in {"proposed", "approved"}
    }

    created = []

    for item in findings:
        key = (str(item.get("title")), "proposed")

        if key in existing:
            continue

        backlog_item = {
            "id": item.get("id"),
            "title": item.get("title"),
            "category": item.get("category"),
            "description": item.get("description"),
            "recommendation": item.get("recommendation"),
            "score": item.get("score"),
            "priority_band": item.get("priority_band"),
            "status": "proposed",
            "owner_approval_required": True,
            "automatic_code_changes": False,
            "automatic_execution": False,
            "external_action_authorized": False,
            "created_at": now(),
            "updated_at": now(),
        }

        backlog.setdefault("items", []).append(backlog_item)
        created.append(backlog_item)
        existing.add(key)

    statuses = ["proposed", "approved", "completed", "rejected"]
    backlog["statistics"] = {
        "total": len(backlog.get("items", [])),
        **{
            status: sum(
                1 for item in backlog.get("items", [])
                if item.get("status") == status
            )
            for status in statuses
        },
    }
    backlog["last_updated_at"] = now()
    save_json(BACKLOG, backlog)

    briefing = {
        "generated_at": now(),
        "headline": (
            f"{len(findings)} improvement opportunity(s) identified; "
            f"{len(created)} added to the backlog."
        ),
        "top_recommendations": findings[:5],
        "critical_count": sum(
            1 for item in findings
            if item.get("priority_band") == "critical"
        ),
        "high_count": sum(
            1 for item in findings
            if item.get("priority_band") == "high"
        ),
        "automatic_code_changes": False,
        "automatic_task_execution": False,
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
            "last_analyzed_at": now(),
            "finding_count": len(findings),
            "created_backlog_count": len(created),
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "continuous_improvement_analysis_complete",
        "finding_count": len(findings),
        "created_backlog_count": len(created),
        "findings": findings,
        "automatic_code_changes": False,
        "automatic_execution": False,
    }

    audit("analyze", result)
    return result


def list_backlog() -> dict[str, Any]:
    store = load_json(BACKLOG, {})
    result = {
        "success": True,
        "status": "continuous_improvement_backlog",
        "statistics": store.get("statistics", {}),
        "items": store.get("items", []),
    }
    audit("list", result)
    return result


def set_status(item_id: str, status_value: str) -> dict[str, Any]:
    allowed = {"approved", "completed", "rejected"}

    if status_value not in allowed:
        result = {
            "success": False,
            "status": "invalid_improvement_status",
            "allowed": sorted(allowed),
        }
        audit("set_status", result)
        return result

    store = load_json(BACKLOG, {})
    item = next(
        (
            entry for entry in store.get("items", [])
            if entry.get("id") == item_id
        ),
        None,
    )

    if not item:
        result = {
            "success": False,
            "status": "improvement_item_not_found",
            "item_id": item_id,
        }
        audit("set_status", result)
        return result

    previous = item.get("status")
    item["status"] = status_value
    item["updated_at"] = now()
    item["automatic_code_changes"] = False
    item["automatic_execution"] = False
    item["external_action_authorized"] = False

    statuses = ["proposed", "approved", "completed", "rejected"]
    store["statistics"] = {
        "total": len(store.get("items", [])),
        **{
            status: sum(
                1 for entry in store.get("items", [])
                if entry.get("status") == status
            )
            for status in statuses
        },
    }
    store["last_updated_at"] = now()
    save_json(BACKLOG, store)

    result = {
        "success": True,
        "status": "improvement_item_updated",
        "item_id": item_id,
        "previous_status": previous,
        "new_status": status_value,
        "automatic_code_changes": False,
        "automatic_execution": False,
    }
    audit("set_status", result)
    return result


def briefing() -> dict[str, Any]:
    data = load_json(BRIEFING, {}).get("briefing")
    result = {
        "success": bool(data),
        "status": "continuous_improvement_briefing",
        "briefing": data,
    }
    audit("briefing", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    health = load_json(HEALTH, {})
    backlog = load_json(BACKLOG, {})

    result = {
        "success": True,
        "status": "continuous_improvement_engine_status",
        "enabled": config.get("enabled", False),
        "automatic_internal_analysis": config.get(
            "automatic_internal_analysis", False
        ),
        "automatic_improvement_recommendations": config.get(
            "automatic_improvement_recommendations", False
        ),
        "automatic_backlog_creation": config.get(
            "automatic_backlog_creation", False
        ),
        "automatic_code_changes": config.get(
            "automatic_code_changes", False
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
        "statistics": backlog.get("statistics", {}),
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
        if action == "analyze":
            return print_result(analyze())

        if action == "list":
            return print_result(list_backlog())

        if action in {"approve", "complete", "reject"}:
            if len(sys.argv) < 3:
                raise ValueError("Improvement item ID is required")

            mapping = {
                "approve": "approved",
                "complete": "completed",
                "reject": "rejected",
            }
            return print_result(
                set_status(sys.argv[2], mapping[action])
            )

        if action == "briefing":
            return print_result(briefing())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_improvement_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "continuous_improvement_error",
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
