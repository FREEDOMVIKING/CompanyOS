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

CONFIG_PATH = MEMORY / "product_execution_config.json"
FACTORY_PROJECTS_PATH = MEMORY / "factory_projects.json"
PLANS_PATH = MEMORY / "product_execution_plans.json"
TASKS_PATH = MEMORY / "product_execution_tasks.json"
HEALTH_PATH = MEMORY / "product_execution_health.json"
AUDIT_PATH = MEMORY / "product_execution_audit.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    temp.replace(path)


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT_PATH, [])

    if not isinstance(records, list):
        records = []

    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })

    save_json(AUDIT_PATH, records[-1000:])


def normalize_projects(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    if isinstance(data, dict):
        for key in (
            "projects",
            "factory_projects",
            "products",
            "items",
        ):
            value = data.get(key)
            if isinstance(value, list):
                return [
                    item for item in value
                    if isinstance(item, dict)
                ]

    return []


def get_projects() -> list[dict[str, Any]]:
    return normalize_projects(
        load_json(FACTORY_PROJECTS_PATH, {})
    )


def find_project(project_id: str) -> dict[str, Any] | None:
    for project in get_projects():
        if project.get("id") == project_id:
            return project

    return None


def latest_project() -> dict[str, Any] | None:
    projects = get_projects()

    if not projects:
        return None

    return projects[-1]


def short_hash(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:12]


def plan_id(project_id: str) -> str:
    return f"plan-{short_hash(project_id)}"


def task_id(project_id: str, order: int, name: str) -> str:
    return f"task-{short_hash(f'{project_id}:{order}:{name}')}"


def task_template(
    project: dict[str, Any],
) -> list[dict[str, Any]]:
    project_name = str(
        project.get("name")
        or project.get("title")
        or "Product"
    )

    mvp_features = project.get("mvp_features", [])

    feature_text = (
        ", ".join(str(item) for item in mvp_features[:5])
        if isinstance(mvp_features, list) and mvp_features
        else "core MVP features"
    )

    return [
        {
            "name": "Define customer and problem validation plan",
            "type": "research",
            "phase": "discovery",
            "priority": 100,
            "description": (
                f"Create the validation plan for {project_name}, "
                "including customer questions, assumptions and success criteria."
            ),
            "deliverables": [
                "Target customer summary",
                "Problem validation checklist",
                "Validation interview questions",
                "Go or hold criteria"
            ]
        },
        {
            "name": "Create product requirements document",
            "type": "design",
            "phase": "planning",
            "priority": 95,
            "description": (
                f"Define the MVP scope for {project_name} using "
                f"these initial features: {feature_text}."
            ),
            "deliverables": [
                "Product requirements document",
                "MVP scope",
                "Out-of-scope list",
                "Acceptance criteria"
            ]
        },
        {
            "name": "Design core user workflow",
            "type": "design",
            "phase": "design",
            "priority": 90,
            "description": (
                "Map the main user journey from first use through "
                "successful completion of the core workflow."
            ),
            "deliverables": [
                "User flow",
                "Screen list",
                "Navigation plan",
                "Error-state plan"
            ]
        },
        {
            "name": "Define project data model",
            "type": "development",
            "phase": "architecture",
            "priority": 88,
            "description": (
                "Define the entities, records and relationships "
                "required by the MVP."
            ),
            "deliverables": [
                "Data model",
                "Field definitions",
                "Storage plan",
                "Data validation rules"
            ]
        },
        {
            "name": "Build MVP project structure",
            "type": "development",
            "phase": "build",
            "priority": 85,
            "description": (
                "Create the initial project structure, configuration, "
                "modules and local runtime."
            ),
            "deliverables": [
                "Runnable project skeleton",
                "Configuration files",
                "Module structure",
                "Local start command"
            ]
        },
        {
            "name": "Build core MVP workflow",
            "type": "development",
            "phase": "build",
            "priority": 82,
            "description": (
                "Implement the primary workflow required to solve "
                "the customer's main problem."
            ),
            "deliverables": [
                "Core workflow implementation",
                "Input validation",
                "State tracking",
                "Basic error handling"
            ]
        },
        {
            "name": "Create internal test suite",
            "type": "testing",
            "phase": "testing",
            "priority": 78,
            "description": (
                "Create repeatable tests for the main product workflow "
                "and expected failure conditions."
            ),
            "deliverables": [
                "Core workflow tests",
                "Validation tests",
                "Failure-path tests",
                "Test report"
            ]
        },
        {
            "name": "Run product validation review",
            "type": "validation",
            "phase": "validation",
            "priority": 74,
            "description": (
                "Review the MVP against the proposal, acceptance criteria "
                "and customer problem."
            ),
            "deliverables": [
                "Validation report",
                "Missing requirements list",
                "Defect list",
                "Go or revise recommendation"
            ]
        },
        {
            "name": "Create product documentation",
            "type": "documentation",
            "phase": "documentation",
            "priority": 70,
            "description": (
                "Create installation, usage and maintenance documentation."
            ),
            "deliverables": [
                "README",
                "Installation instructions",
                "User instructions",
                "Maintenance notes"
            ]
        },
        {
            "name": "Create deployment and launch checklist",
            "type": "deployment_planning",
            "phase": "launch_planning",
            "priority": 65,
            "description": (
                "Prepare an internal deployment and launch checklist. "
                "No external publication is authorized."
            ),
            "deliverables": [
                "Deployment checklist",
                "Launch readiness checklist",
                "Rollback plan",
                "Owner approval requirements"
            ]
        },
    ]


def update_plan_statistics(store: dict[str, Any]) -> None:
    plans = store.get("plans", [])

    store["statistics"] = {
        "total": len(plans),
        "planned": sum(
            1 for item in plans
            if item.get("status") == "planned"
        ),
        "active": sum(
            1 for item in plans
            if item.get("status") == "active"
        ),
        "completed": sum(
            1 for item in plans
            if item.get("status") == "completed"
        ),
        "blocked": sum(
            1 for item in plans
            if item.get("status") == "blocked"
        ),
    }

    store["last_updated_at"] = now()


def update_task_statistics(store: dict[str, Any]) -> None:
    tasks = store.get("tasks", [])

    store["statistics"] = {
        "total": len(tasks),
        "pending": sum(
            1 for item in tasks
            if item.get("status") == "pending"
        ),
        "in_progress": sum(
            1 for item in tasks
            if item.get("status") == "in_progress"
        ),
        "completed": sum(
            1 for item in tasks
            if item.get("status") == "completed"
        ),
        "blocked": sum(
            1 for item in tasks
            if item.get("status") == "blocked"
        ),
        "failed": sum(
            1 for item in tasks
            if item.get("status") == "failed"
        ),
    }

    store["last_updated_at"] = now()


def create_plan(project_id: str) -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "product_execution_disabled",
        }
        audit("plan", result)
        return result

    project = find_project(project_id)

    if not project:
        result = {
            "success": False,
            "status": "factory_project_not_found",
            "project_id": project_id,
        }
        audit("plan", result)
        return result

    plans_store = load_json(
        PLANS_PATH,
        {
            "schema_version": 1,
            "plans": [],
            "statistics": {},
        },
    )

    tasks_store = load_json(
        TASKS_PATH,
        {
            "schema_version": 1,
            "tasks": [],
            "statistics": {},
        },
    )

    plans = plans_store.setdefault("plans", [])
    tasks = tasks_store.setdefault("tasks", [])

    new_plan_id = plan_id(project_id)

    for existing in plans:
        if existing.get("id") == new_plan_id:
            result = {
                "success": True,
                "status": "execution_plan_already_exists",
                "plan": existing,
            }
            audit("plan", result)
            return result

    templates = task_template(project)
    created_tasks: list[dict[str, Any]] = []

    for order, template in enumerate(templates, start=1):
        new_task = {
            "id": task_id(
                project_id,
                order,
                template["name"],
            ),
            "plan_id": new_plan_id,
            "project_id": project_id,
            "project_name": (
                project.get("name")
                or project.get("title")
            ),
            "order": order,
            "name": template["name"],
            "type": template["type"],
            "phase": template["phase"],
            "priority": template["priority"],
            "description": template["description"],
            "deliverables": template["deliverables"],
            "status": "pending",
            "blocked_by": (
                []
                if order == 1
                else [
                    created_tasks[-1]["id"]
                ]
            ),
            "internal_execution_allowed": True,
            "external_execution_allowed": False,
            "external_spending_allowed": False,
            "external_publication_allowed": False,
            "attempts": 0,
            "result": None,
            "last_error": None,
            "created_at": now(),
            "updated_at": now(),
        }

        tasks.append(new_task)
        created_tasks.append(new_task)

    plan = {
        "id": new_plan_id,
        "project_id": project_id,
        "project_name": (
            project.get("name")
            or project.get("title")
        ),
        "status": "planned",
        "current_phase": "discovery",
        "task_ids": [
            item["id"]
            for item in created_tasks
        ],
        "total_tasks": len(created_tasks),
        "completed_tasks": 0,
        "progress_percent": 0,
        "internal_execution_allowed": True,
        "automatic_internal_execution": False,
        "automatic_external_execution": False,
        "automatic_spending": False,
        "automatic_publication": False,
        "created_at": now(),
        "updated_at": now(),
    }

    plans.append(plan)

    update_plan_statistics(plans_store)
    update_task_statistics(tasks_store)

    save_json(PLANS_PATH, plans_store)
    save_json(TASKS_PATH, tasks_store)

    health = {
        "healthy": True,
        "last_planned_at": now(),
        "last_error": None,
        "latest_plan_id": new_plan_id,
        "latest_project_id": project_id,
        "tasks_created": len(created_tasks),
    }
    save_json(HEALTH_PATH, health)

    result = {
        "success": True,
        "status": "product_execution_plan_created",
        "plan_id": new_plan_id,
        "project_id": project_id,
        "project_name": plan["project_name"],
        "tasks_created": len(created_tasks),
        "automatic_internal_execution": False,
        "automatic_external_execution": False,
        "automatic_spending": False,
        "automatic_publication": False,
    }

    audit("plan", result)
    return result


def create_latest_plan() -> dict[str, Any]:
    project = latest_project()

    if not project:
        result = {
            "success": False,
            "status": "no_factory_projects_available",
        }
        audit("plan_latest", result)
        return result

    return create_plan(str(project.get("id")))


def recalculate_plan(plan_id_value: str) -> None:
    plans_store = load_json(PLANS_PATH, {})
    tasks_store = load_json(TASKS_PATH, {})

    tasks = [
        item
        for item in tasks_store.get("tasks", [])
        if item.get("plan_id") == plan_id_value
    ]

    for plan in plans_store.get("plans", []):
        if plan.get("id") != plan_id_value:
            continue

        completed = sum(
            1 for item in tasks
            if item.get("status") == "completed"
        )

        blocked = sum(
            1 for item in tasks
            if item.get("status") == "blocked"
        )

        in_progress = sum(
            1 for item in tasks
            if item.get("status") == "in_progress"
        )

        total = len(tasks)

        plan["completed_tasks"] = completed
        plan["total_tasks"] = total
        plan["progress_percent"] = (
            round((completed / total) * 100, 2)
            if total
            else 0
        )

        remaining = [
            item
            for item in tasks
            if item.get("status") != "completed"
        ]

        if completed == total and total:
            plan["status"] = "completed"
            plan["current_phase"] = "complete"
            plan["completed_at"] = now()

        elif blocked:
            plan["status"] = "blocked"

        elif in_progress:
            plan["status"] = "active"

        else:
            plan["status"] = "planned"

        if remaining:
            plan["current_phase"] = remaining[0].get(
                "phase",
                "unknown",
            )

        plan["updated_at"] = now()

    update_plan_statistics(plans_store)
    save_json(PLANS_PATH, plans_store)


def task_dependencies_complete(
    task: dict[str, Any],
    all_tasks: list[dict[str, Any]],
) -> bool:
    dependencies = task.get("blocked_by", [])

    if not dependencies:
        return True

    statuses = {
        item.get("id"): item.get("status")
        for item in all_tasks
    }

    return all(
        statuses.get(dependency) == "completed"
        for dependency in dependencies
    )


def start_task(task_id_value: str) -> dict[str, Any]:
    store = load_json(TASKS_PATH, {})
    tasks = store.get("tasks", [])

    for task in tasks:
        if task.get("id") != task_id_value:
            continue

        if task.get("status") == "completed":
            result = {
                "success": True,
                "status": "task_already_completed",
                "task": task,
            }
            audit("start_task", result)
            return result

        if not task_dependencies_complete(task, tasks):
            result = {
                "success": False,
                "status": "task_dependency_blocked",
                "task_id": task_id_value,
                "blocked_by": task.get("blocked_by", []),
            }
            audit("start_task", result)
            return result

        task["status"] = "in_progress"
        task["started_at"] = now()
        task["updated_at"] = now()
        task["attempts"] = int(task.get("attempts", 0)) + 1

        update_task_statistics(store)
        save_json(TASKS_PATH, store)
        recalculate_plan(str(task.get("plan_id")))

        result = {
            "success": True,
            "status": "task_started",
            "task_id": task_id_value,
            "name": task.get("name"),
            "type": task.get("type"),
            "internal_execution_allowed": True,
            "external_execution_allowed": False,
        }

        audit("start_task", result)
        return result

    result = {
        "success": False,
        "status": "task_not_found",
        "task_id": task_id_value,
    }
    audit("start_task", result)
    return result


def complete_task(
    task_id_value: str,
    result_text: str | None,
) -> dict[str, Any]:
    store = load_json(TASKS_PATH, {})
    tasks = store.get("tasks", [])

    for task in tasks:
        if task.get("id") != task_id_value:
            continue

        if not task_dependencies_complete(task, tasks):
            result = {
                "success": False,
                "status": "task_dependency_blocked",
                "task_id": task_id_value,
                "blocked_by": task.get("blocked_by", []),
            }
            audit("complete_task", result)
            return result

        task["status"] = "completed"
        task["result"] = (
            result_text
            or "Task completed through internal execution workflow"
        )
        task["completed_at"] = now()
        task["updated_at"] = now()
        task["last_error"] = None

        update_task_statistics(store)
        save_json(TASKS_PATH, store)
        recalculate_plan(str(task.get("plan_id")))

        result = {
            "success": True,
            "status": "task_completed",
            "task_id": task_id_value,
            "name": task.get("name"),
            "result": task.get("result"),
        }

        audit("complete_task", result)
        return result

    result = {
        "success": False,
        "status": "task_not_found",
        "task_id": task_id_value,
    }
    audit("complete_task", result)
    return result


def next_task(plan_id_value: str | None = None) -> dict[str, Any]:
    store = load_json(TASKS_PATH, {})
    tasks = store.get("tasks", [])

    candidates = [
        task
        for task in tasks
        if task.get("status") == "pending"
        and (
            plan_id_value is None
            or task.get("plan_id") == plan_id_value
        )
        and task_dependencies_complete(task, tasks)
    ]

    candidates.sort(
        key=lambda item: (
            -int(item.get("priority", 0)),
            int(item.get("order", 999)),
        )
    )

    task = candidates[0] if candidates else None

    result = {
        "success": bool(task),
        "status": (
            "next_execution_task"
            if task
            else "no_ready_tasks"
        ),
        "task": task,
    }

    audit("next", result)
    return result


def list_tasks(
    plan_id_value: str | None = None,
) -> dict[str, Any]:
    store = load_json(TASKS_PATH, {})
    tasks = store.get("tasks", [])

    if plan_id_value:
        tasks = [
            item
            for item in tasks
            if item.get("plan_id") == plan_id_value
        ]

    result = {
        "success": True,
        "status": "product_execution_task_list",
        "count": len(tasks),
        "statistics": store.get("statistics", {}),
        "tasks": [
            {
                "id": item.get("id"),
                "plan_id": item.get("plan_id"),
                "order": item.get("order"),
                "name": item.get("name"),
                "type": item.get("type"),
                "phase": item.get("phase"),
                "priority": item.get("priority"),
                "status": item.get("status"),
                "blocked_by": item.get("blocked_by"),
            }
            for item in tasks
        ],
    }

    audit("tasks", result)
    return result


def list_plans() -> dict[str, Any]:
    store = load_json(PLANS_PATH, {})
    plans = store.get("plans", [])

    result = {
        "success": True,
        "status": "product_execution_plan_list",
        "count": len(plans),
        "statistics": store.get("statistics", {}),
        "plans": [
            {
                "id": item.get("id"),
                "project_id": item.get("project_id"),
                "project_name": item.get("project_name"),
                "status": item.get("status"),
                "current_phase": item.get("current_phase"),
                "total_tasks": item.get("total_tasks"),
                "completed_tasks": item.get("completed_tasks"),
                "progress_percent": item.get("progress_percent"),
            }
            for item in plans
        ],
    }

    audit("plans", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})
    plans = load_json(PLANS_PATH, {})
    tasks = load_json(TASKS_PATH, {})
    health = load_json(HEALTH_PATH, {})

    result = {
        "success": True,
        "status": "product_execution_pipeline_status",
        "enabled": config.get("enabled", False),
        "automatic_planning": config.get(
            "automatic_planning",
            False,
        ),
        "automatic_internal_execution": config.get(
            "automatic_internal_execution",
            False,
        ),
        "automatic_external_execution": config.get(
            "automatic_external_execution",
            False,
        ),
        "automatic_spending": config.get(
            "automatic_spending",
            False,
        ),
        "automatic_publication": config.get(
            "automatic_publication",
            False,
        ),
        "plan_statistics": plans.get("statistics", {}),
        "task_statistics": tasks.get("statistics", {}),
        "health": health,
    }

    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: product_execution_pipeline.py "
            "plan <project_id>|plan-latest|plans|tasks [plan_id]|"
            "next [plan_id]|start <task_id>|"
            "complete <task_id> [result]|status"
        )
        return 2

    action = sys.argv[1].lower()

    try:
        if action == "plan":
            if len(sys.argv) < 3:
                raise ValueError("Project ID is required")
            return print_result(create_plan(sys.argv[2]))

        if action == "plan-latest":
            return print_result(create_latest_plan())

        if action == "plans":
            return print_result(list_plans())

        if action == "tasks":
            selected_plan = (
                sys.argv[2]
                if len(sys.argv) > 2
                else None
            )
            return print_result(list_tasks(selected_plan))

        if action == "next":
            selected_plan = (
                sys.argv[2]
                if len(sys.argv) > 2
                else None
            )
            return print_result(next_task(selected_plan))

        if action == "start":
            if len(sys.argv) < 3:
                raise ValueError("Task ID is required")
            return print_result(start_task(sys.argv[2]))

        if action == "complete":
            if len(sys.argv) < 3:
                raise ValueError("Task ID is required")

            result_text = (
                " ".join(sys.argv[3:]).strip()
                if len(sys.argv) > 3
                else None
            )

            return print_result(
                complete_task(
                    sys.argv[2],
                    result_text,
                )
            )

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_execution_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "product_execution_error",
            "action": action,
            "error": str(exc),
        }

        save_json(
            HEALTH_PATH,
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
