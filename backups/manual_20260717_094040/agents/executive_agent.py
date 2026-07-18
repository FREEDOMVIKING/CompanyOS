#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE_DIR / "ceo_memory"

TASKS_FILE = MEMORY_DIR / "tasks.json"
RESULTS_FILE = MEMORY_DIR / "agent_results.json"
PROJECTS_FILE = MEMORY_DIR / "projects.json"
FINANCE_FILE = MEMORY_DIR / "finance.json"
ESCALATIONS_FILE = MEMORY_DIR / "escalations.json"

REPORT_DIR = MEMORY_DIR / "executive_reports"
LATEST_REPORT_FILE = MEMORY_DIR / "executive_summary.json"

DEPARTMENTS = {
    "research": {
        "executive": "Chief Research Officer",
        "agents": ["research_agent", "validation_agent"],
    },
    "technology": {
        "executive": "Chief Technology Officer",
        "agents": ["builder_agent", "recovery_agent"],
    },
    "operations": {
        "executive": "Chief Operating Officer",
        "agents": ["builder_agent", "auditor_agent"],
    },
    "marketing": {
        "executive": "Chief Marketing Officer",
        "agents": ["marketing_agent"],
    },
    "finance": {
        "executive": "Chief Financial Officer",
        "agents": ["finance_agent"],
    },
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    temporary.replace(path)


def normalize_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        return [item for item in value.values() if isinstance(item, dict)]

    return []


def get_status(item: dict[str, Any]) -> str:
    return str(item.get("status", "unknown")).lower()


def get_result_success(result: dict[str, Any]) -> bool | None:
    value = result.get("success")

    if isinstance(value, bool):
        return value

    inner = result.get("result")

    if isinstance(inner, dict):
        inner_value = inner.get("success")

        if isinstance(inner_value, bool):
            return inner_value

    return None


def create_department_report(
    department_name: str,
    settings: dict[str, Any],
    tasks: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    agents = set(settings["agents"])

    department_tasks = [
        task for task in tasks
        if task.get("agent") in agents
    ]

    department_results = [
        result for result in results
        if result.get("agent") in agents
    ]

    pending = [
        task for task in department_tasks
        if get_status(task) in {"pending", "queued", "waiting"}
    ]

    running = [
        task for task in department_tasks
        if get_status(task) == "running"
    ]

    completed = [
        task for task in department_tasks
        if get_status(task) in {
            "completed",
            "done",
            "success",
            "successful",
        }
    ]

    failed_tasks = [
        task for task in department_tasks
        if get_status(task) in {"failed", "error", "rejected"}
    ]

    successful_results = [
        result for result in department_results
        if get_result_success(result) is True
    ]

    failed_results = [
        result for result in department_results
        if get_result_success(result) is False
    ]

    if failed_results:
        health = "attention_required"
    elif pending or running:
        health = "active"
    else:
        health = "stable"

    recommendations = []

    if failed_results:
        recommendations.append(
            "Review failed results and recovery status."
        )

    if len(pending) > 5:
        recommendations.append(
            "Reduce the department backlog."
        )

    if not department_tasks:
        recommendations.append(
            "No tasks have been assigned to this department."
        )

    if not recommendations:
        recommendations.append(
            "Continue normal department operations."
        )

    return {
        "department": department_name,
        "executive": settings["executive"],
        "agents": settings["agents"],
        "health": health,
        "task_counts": {
            "total": len(department_tasks),
            "pending": len(pending),
            "running": len(running),
            "completed": len(completed),
            "failed": len(failed_tasks),
        },
        "result_counts": {
            "total": len(department_results),
            "successful": len(successful_results),
            "failed": len(failed_results),
        },
        "recommendations": recommendations,
    }


def executive_review() -> dict[str, Any]:
    tasks = normalize_list(load_json(TASKS_FILE, []))
    results = normalize_list(load_json(RESULTS_FILE, []))
    projects = normalize_list(load_json(PROJECTS_FILE, []))
    escalations = normalize_list(load_json(ESCALATIONS_FILE, []))

    finance = load_json(FINANCE_FILE, {})

    if not isinstance(finance, dict):
        finance = {}

    open_escalations = [
        escalation
        for escalation in escalations
        if get_status(escalation) == "open"
    ]

    departments = {
        name: create_department_report(
            name,
            settings,
            tasks,
            results,
        )
        for name, settings in DEPARTMENTS.items()
    }

    attention_departments = [
        name
        for name, report in departments.items()
        if report["health"] == "attention_required"
    ]

    active_projects = [
        project
        for project in projects
        if get_status(project) not in {
            "completed",
            "cancelled",
            "failed",
            "archived",
        }
    ]

    pending_tasks = [
        task
        for task in tasks
        if get_status(task) in {"pending", "queued", "waiting"}
    ]

    priorities = []

    if open_escalations:
        priorities.append({
            "priority": 1,
            "action": "resolve_escalations",
            "count": len(open_escalations),
        })

    if attention_departments:
        priorities.append({
            "priority": 2,
            "action": "review_departments",
            "departments": attention_departments,
        })

    if pending_tasks:
        priorities.append({
            "priority": 3,
            "action": "complete_pending_tasks",
            "count": len(pending_tasks),
        })

    if not priorities:
        priorities.append({
            "priority": 1,
            "action": "continue_business_validation",
            "reason": "No critical operating issues detected",
        })

    summary = {
        "success": True,
        "status": "executive_review_complete",
        "reviewed_at": now(),
        "company_health": (
            "attention_required"
            if open_escalations or attention_departments
            else "stable"
        ),
        "department_reports": departments,
        "company_priorities": priorities,
        "active_projects": len(active_projects),
        "total_projects": len(projects),
        "pending_tasks": len(pending_tasks),
        "open_escalations": len(open_escalations),
        "available_budget_usd": float(
            finance.get("available_budget_usd", 0) or 0
        ),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    filename = (
        "executive_report_"
        + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        + ".json"
    )

    report_file = REPORT_DIR / filename

    save_json(report_file, summary)
    save_json(LATEST_REPORT_FILE, summary)

    summary["report_file"] = str(report_file)

    return summary


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action in {
        "executive_review",
        "review_departments",
        "create_executive_report",
    }:
        return executive_review()

    return {
        "success": False,
        "error": f"Unsupported executive action: {action}",
    }


if __name__ == "__main__":
    print(json.dumps(executive_review(), indent=2))
