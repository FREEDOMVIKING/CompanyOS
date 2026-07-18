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

CONFIG = MEMORY / "business_automation_config.json"
STATE = MEMORY / "business_automation_state.json"
FEED = MEMORY / "business_activity_feed.json"
SUMMARY = MEMORY / "daily_executive_summary.json"
HEALTH = MEMORY / "business_automation_health.json"
AUDIT = MEMORY / "business_automation_audit.json"

LEADS = MEMORY / "crm_leads.json"
QUOTES = MEMORY / "quote_registry.json"
PROJECTS = MEMORY / "project_registry.json"
MILESTONES = MEMORY / "project_milestones.json"
FOLLOWUPS = MEMORY / "sales_followups.json"
TASKS = MEMORY / "product_execution_tasks.json"


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


def make_id(prefix: str, seed: str) -> str:
    digest = hashlib.sha256(
        f"{seed}:{now()}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{prefix}-{digest}"


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


def add_feed(
    activity_type: str,
    title: str,
    details: dict[str, Any],
) -> None:
    store = load_json(
        FEED,
        {
            "schema_version": 1,
            "activities": [],
            "last_updated_at": None,
        },
    )

    store.setdefault("activities", []).append({
        "id": make_id("activity", title),
        "activity_type": activity_type,
        "title": title,
        "details": details,
        "created_at": now(),
    })

    store["activities"] = store["activities"][-1000:]
    store["last_updated_at"] = now()
    save_json(FEED, store)


def ensure_internal_task(
    name: str,
    description: str,
    source_id: str,
) -> bool:
    store = load_json(
        TASKS,
        {
            "schema_version": 1,
            "tasks": [],
            "statistics": {},
        },
    )

    tasks = store.setdefault("tasks", [])

    if any(
        item.get("source_id") == source_id
        and item.get("name") == name
        for item in tasks
    ):
        return False

    tasks.append({
        "id": make_id("task", f"{source_id}:{name}"),
        "name": name,
        "description": description,
        "source_id": source_id,
        "type": "business_automation",
        "status": "pending",
        "internal_execution_allowed": True,
        "external_execution_allowed": False,
        "created_at": now(),
        "updated_at": now(),
    })

    save_json(TASKS, store)
    return True


def ensure_quote_project_link(
    quote: dict[str, Any],
    projects: list[dict[str, Any]],
) -> bool:
    quote_id = str(quote.get("id"))

    linked = next(
        (
            item
            for item in projects
            if item.get("source_quote_id") == quote_id
        ),
        None,
    )

    if linked:
        return False

    project_id = make_id(
        "project",
        f"{quote.get('customer_name')}:{quote.get('project_name')}",
    )

    projects.append({
        "id": project_id,
        "customer_name": quote.get("customer_name"),
        "project_name": quote.get("project_name"),
        "amount": quote.get("amount"),
        "source_quote_id": quote_id,
        "status": "planning",
        "progress_percent": 0,
        "health": "needs_review",
        "customer_portal_enabled": False,
        "external_file_sharing_enabled": False,
        "customer_notifications_enabled": False,
        "created_at": now(),
        "updated_at": now(),
    })

    add_feed(
        "project_created",
        "Project created from quote",
        {
            "quote_id": quote_id,
            "project_id": project_id,
            "project_name": quote.get("project_name"),
        },
    )

    return True


def ensure_project_milestones(
    project: dict[str, Any],
    milestones: list[dict[str, Any]],
) -> int:
    existing = {
        item.get("title")
        for item in milestones
        if item.get("project_id") == project.get("id")
    }

    defaults = [
        ("Confirm scope", "Review and confirm final project scope."),
        ("Schedule work", "Create internal schedule and resource plan."),
        ("Execute work", "Complete internal project work."),
        ("Final review", "Run completion and quality review."),
    ]

    created = 0

    for title, description in defaults:
        if title in existing:
            continue

        milestones.append({
            "id": make_id(
                "milestone",
                f"{project.get('id')}:{title}",
            ),
            "project_id": project.get("id"),
            "title": title,
            "description": description,
            "status": "pending",
            "created_at": now(),
            "updated_at": now(),
        })

        created += 1

    if created:
        add_feed(
            "milestones_created",
            "Project milestones generated",
            {
                "project_id": project.get("id"),
                "count": created,
            },
        )

    return created


def run_cycle() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "business_automation_disabled",
        }
        audit("cycle", result)
        return result

    state = load_json(
        STATE,
        {
            "schema_version": 1,
            "processed_leads": [],
            "processed_quotes": [],
            "processed_projects": [],
            "last_cycle_at": None,
        },
    )

    leads_store = load_json(LEADS, {"leads": []})
    quotes_store = load_json(QUOTES, {"quotes": []})
    projects_store = load_json(PROJECTS, {"projects": []})
    milestones_store = load_json(MILESTONES, {"milestones": []})

    leads = leads_store.setdefault("leads", [])
    quotes = quotes_store.setdefault("quotes", [])
    projects = projects_store.setdefault("projects", [])
    milestones = milestones_store.setdefault("milestones", [])

    tasks_created = 0
    projects_created = 0
    milestones_created = 0

    for lead in leads:
        lead_id = str(lead.get("id"))

        if lead_id not in state["processed_leads"]:
            if ensure_internal_task(
                "Review new lead",
                f"Review lead for {lead.get('customer_name')} - "
                f"{lead.get('project_name')}.",
                lead_id,
            ):
                tasks_created += 1

            add_feed(
                "lead_processed",
                "Lead added to business workflow",
                {
                    "lead_id": lead_id,
                    "customer_name": lead.get("customer_name"),
                    "project_name": lead.get("project_name"),
                },
            )

            state["processed_leads"].append(lead_id)

    for quote in quotes:
        quote_id = str(quote.get("id"))

        if quote_id not in state["processed_quotes"]:
            if ensure_internal_task(
                "Review quote",
                f"Review quote {quote_id} before any customer delivery.",
                quote_id,
            ):
                tasks_created += 1

            if config.get("automatic_quote_to_project_linking", True):
                if ensure_quote_project_link(quote, projects):
                    projects_created += 1

            state["processed_quotes"].append(quote_id)

    for project in projects:
        project_id = str(project.get("id"))

        if config.get("automatic_milestone_generation", True):
            milestones_created += ensure_project_milestones(
                project,
                milestones,
            )

        if project_id not in state["processed_projects"]:
            if ensure_internal_task(
                "Review project plan",
                f"Review project plan for {project.get('project_name')}.",
                project_id,
            ):
                tasks_created += 1

            state["processed_projects"].append(project_id)

    save_json(PROJECTS, projects_store)
    save_json(MILESTONES, milestones_store)

    state["last_cycle_at"] = now()
    save_json(STATE, state)

    summary = generate_summary()

    save_json(
        HEALTH,
        {
            "healthy": True,
            "last_cycle_at": now(),
            "tasks_created": tasks_created,
            "projects_created": projects_created,
            "milestones_created": milestones_created,
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "business_automation_cycle_complete",
        "tasks_created": tasks_created,
        "projects_created": projects_created,
        "milestones_created": milestones_created,
        "summary_status": summary.get("status"),
        "automatic_customer_notifications": False,
        "automatic_email": False,
        "automatic_sms": False,
        "automatic_external_execution": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    audit("cycle", result)
    return result


def generate_summary() -> dict[str, Any]:
    leads = load_json(LEADS, {}).get("leads", [])
    quotes = load_json(QUOTES, {}).get("quotes", [])
    projects = load_json(PROJECTS, {}).get("projects", [])
    milestones = load_json(MILESTONES, {}).get("milestones", [])
    followups = load_json(FOLLOWUPS, {}).get("followups", [])
    tasks = load_json(TASKS, {}).get("tasks", [])

    summary = {
        "generated_at": now(),
        "lead_count": len(leads),
        "quote_count": len(quotes),
        "project_count": len(projects),
        "milestone_count": len(milestones),
        "pending_followups": sum(
            1 for item in followups
            if item.get("status") == "pending"
        ),
        "pending_internal_tasks": sum(
            1 for item in tasks
            if item.get("status") == "pending"
        ),
        "active_pipeline_value": round(
            sum(
                float(item.get("estimate_amount") or 0)
                for item in leads
                if item.get("status") not in {"won", "lost"}
            ),
            2,
        ),
        "project_completion_average": round(
            (
                sum(
                    int(item.get("progress_percent") or 0)
                    for item in projects
                )
                / len(projects)
            )
            if projects
            else 0,
            2,
        ),
        "external_actions_executed": 0,
        "automatic_spending_executed": 0,
    }

    save_json(
        SUMMARY,
        {
            "schema_version": 1,
            "summary": summary,
            "last_updated_at": now(),
        },
    )

    result = {
        "success": True,
        "status": "daily_executive_summary_generated",
        "summary": summary,
    }

    audit("summary", result)
    return result


def feed() -> dict[str, Any]:
    store = load_json(FEED, {})
    result = {
        "success": True,
        "status": "business_activity_feed",
        "count": len(store.get("activities", [])),
        "activities": store.get("activities", []),
    }
    audit("feed", result)
    return result


def summary() -> dict[str, Any]:
    store = load_json(SUMMARY, {})
    result = {
        "success": bool(store.get("summary")),
        "status": "daily_executive_summary",
        "summary": store.get("summary"),
    }
    audit("summary_view", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    state = load_json(STATE, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "business_automation_status",
        "enabled": config.get("enabled", False),
        "automatic_internal_task_creation": config.get(
            "automatic_internal_task_creation", False
        ),
        "automatic_quote_to_project_linking": config.get(
            "automatic_quote_to_project_linking", False
        ),
        "automatic_milestone_generation": config.get(
            "automatic_milestone_generation", False
        ),
        "automatic_customer_notifications": config.get(
            "automatic_customer_notifications", False
        ),
        "automatic_email": config.get("automatic_email", False),
        "automatic_sms": config.get("automatic_sms", False),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_publication": config.get(
            "automatic_publication", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "state": state,
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
        if action == "run":
            return print_result(run_cycle())

        if action == "summary":
            return print_result(generate_summary())

        if action == "show-summary":
            return print_result(summary())

        if action == "feed":
            return print_result(feed())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_automation_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "business_automation_error",
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
