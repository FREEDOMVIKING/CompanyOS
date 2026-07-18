#!/usr/bin/env python3

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE_DIR / "ceo_memory"
VENTURES_DIR = BASE_DIR / "company_ventures"

IDEAS_FILE = MEMORY_DIR / "ideas.json"
SCORES_FILE = MEMORY_DIR / "opportunity_scores.json"
PROJECTS_FILE = MEMORY_DIR / "projects.json"
TASKS_FILE = MEMORY_DIR / "tasks.json"
FINANCE_FILE = MEMORY_DIR / "finance.json"

VENTURES_FILE = MEMORY_DIR / "ventures.json"
INCUBATOR_STATE_FILE = MEMORY_DIR / "incubator_state.json"
LATEST_REPORT_FILE = MEMORY_DIR / "incubator_summary.json"
REPORT_DIR = MEMORY_DIR / "incubator_reports"


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
        return [
            item
            for item in value
            if isinstance(item, dict)
        ]

    if isinstance(value, dict):
        return [
            item
            for item in value.values()
            if isinstance(item, dict)
        ]

    return []


def slugify(value: str) -> str:
    cleaned = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        value.strip().lower(),
    )

    return cleaned.strip("_") or "unnamed_venture"


def find_idea(
    ideas: list[dict[str, Any]],
    idea_id: str,
) -> dict[str, Any] | None:
    return next(
        (
            idea
            for idea in ideas
            if str(idea.get("id", "")) == idea_id
        ),
        None,
    )


def find_score(
    scores: list[dict[str, Any]],
    idea_id: str,
) -> dict[str, Any] | None:
    return next(
        (
            score
            for score in scores
            if str(score.get("idea_id", "")) == idea_id
        ),
        None,
    )


def create_task(
    agent: str,
    action: str,
    project_id: str,
    payload: dict[str, Any],
    priority: int,
) -> dict[str, Any]:
    return {
        "id": f"task-{uuid.uuid4().hex[:10]}",
        "agent": agent,
        "action": action,
        "project_id": project_id,
        "payload": payload,
        "priority": priority,
        "status": "pending",
        "retry_count": 0,
        "created_at": now(),
        "started_at": None,
        "completed_at": None,
    }


def default_milestones() -> list[dict[str, Any]]:
    return [
        {
            "id": "milestone-1",
            "name": "Customer problem validation",
            "status": "pending",
            "owner": "validation_agent",
            "completion_requirement": (
                "At least five customer or market observations"
            ),
        },
        {
            "id": "milestone-2",
            "name": "Minimum viable prototype",
            "status": "pending",
            "owner": "builder_agent",
            "completion_requirement": (
                "A working prototype with basic tests"
            ),
        },
        {
            "id": "milestone-3",
            "name": "Quality and safety audit",
            "status": "pending",
            "owner": "auditor_agent",
            "completion_requirement": (
                "Prototype passes required audit checks"
            ),
        },
        {
            "id": "milestone-4",
            "name": "Market validation plan",
            "status": "pending",
            "owner": "marketing_agent",
            "completion_requirement": (
                "Launch plan and customer outreach draft created"
            ),
        },
        {
            "id": "milestone-5",
            "name": "Financial readiness review",
            "status": "pending",
            "owner": "finance_agent",
            "completion_requirement": (
                "Budget and spending limits reviewed"
            ),
        },
    ]


def create_workspace_files(
    venture_dir: Path,
    venture: dict[str, Any],
) -> list[str]:
    venture_dir.mkdir(parents=True, exist_ok=False)

    profile = {
        "venture_id": venture["id"],
        "project_id": venture["project_id"],
        "idea_id": venture["idea_id"],
        "name": venture["name"],
        "problem": venture["problem"],
        "solution": venture["solution"],
        "target_customer": venture["target_customer"],
        "score": venture["opportunity_score"],
        "status": venture["status"],
        "stage": venture["stage"],
        "created_at": venture["created_at"],
    }

    launch_plan = {
        "venture_id": venture["id"],
        "objective": "Validate demand before significant spending",
        "phases": [
            {
                "phase": 1,
                "name": "Research",
                "maximum_cost_usd": 0,
            },
            {
                "phase": 2,
                "name": "Prototype",
                "maximum_cost_usd": 5,
            },
            {
                "phase": 3,
                "name": "Validation",
                "maximum_cost_usd": 5,
            },
        ],
        "success_requirements": {
            "minimum_customer_observations": 5,
            "minimum_expressions_of_interest": 2,
            "prototype_audit_required": True,
        },
    }

    readme = f"""# {venture["name"]}

## Venture ID
{venture["id"]}

## Problem
{venture["problem"]}

## Proposed solution
{venture["solution"]}

## Target customer
{venture["target_customer"]}

## Opportunity score
{venture["opportunity_score"]} / 10

## Current stage
{venture["stage"]}

## Operating rule
Validate demand before committing significant money or external resources.
"""

    files = {
        "venture.json": profile,
        "milestones.json": venture["milestones"],
        "launch_plan.json": launch_plan,
    }

    for filename, data in files.items():
        save_json(venture_dir / filename, data)

    (venture_dir / "README.md").write_text(
        readme,
        encoding="utf-8",
    )

    return [
        "README.md",
        "venture.json",
        "milestones.json",
        "launch_plan.json",
    ]


def incubate_idea(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    idea_id = str(payload.get("idea_id", "")).strip()

    if not idea_id:
        return {
            "success": False,
            "error": "idea_id is required",
        }

    minimum_score = float(
        payload.get("minimum_score", 5.0)
    )

    ideas = normalize_list(load_json(IDEAS_FILE, []))
    scores = normalize_list(load_json(SCORES_FILE, []))
    projects = normalize_list(load_json(PROJECTS_FILE, []))
    tasks = normalize_list(load_json(TASKS_FILE, []))
    ventures = normalize_list(load_json(VENTURES_FILE, []))
    finance = load_json(FINANCE_FILE, {})

    idea = find_idea(ideas, idea_id)

    if idea is None:
        return {
            "success": False,
            "error": f"Idea not found: {idea_id}",
        }

    existing = next(
        (
            venture
            for venture in ventures
            if str(venture.get("idea_id", "")) == idea_id
            and str(venture.get("status", "")).lower()
            not in {"cancelled", "failed", "archived"}
        ),
        None,
    )

    if existing:
        return {
            "success": False,
            "error": (
                f"An active venture already exists for {idea_id}: "
                f"{existing.get('id')}"
            ),
        }

    score_record = find_score(scores, idea_id)
    opportunity_score = float(
        score_record.get("final_score", 0)
        if score_record
        else 0
    )

    if opportunity_score < minimum_score:
        return {
            "success": False,
            "status": "score_below_threshold",
            "idea_id": idea_id,
            "opportunity_score": opportunity_score,
            "minimum_score": minimum_score,
            "error": "Idea did not meet the incubation threshold",
        }

    name = str(
        idea.get("name", f"Venture for {idea_id}")
    ).strip()

    slug = slugify(name)
    venture_id = f"venture-{uuid.uuid4().hex[:10]}"
    project_id = f"project-{uuid.uuid4().hex[:8]}"
    prototype_slug = f"{slug}_{venture_id[-4:]}"

    venture_dir = (VENTURES_DIR / slug).resolve()

    if venture_dir.parent != VENTURES_DIR.resolve():
        return {
            "success": False,
            "error": "Invalid venture workspace path",
        }

    if venture_dir.exists():
        venture_dir = (
            VENTURES_DIR
            / f"{slug}_{venture_id[-4:]}"
        ).resolve()

    problem = str(
        idea.get(
            "problem",
            idea.get(
                "description",
                "Customer problem requires validation",
            ),
        )
    )

    solution = str(
        idea.get(
            "solution",
            "Create a focused digital product or service",
        )
    )

    target_customer = str(
        idea.get(
            "target_customer",
            "Target customer requires further research",
        )
    )

    available_budget = 0.0

    if isinstance(finance, dict):
        available_budget = float(
            finance.get("available_budget_usd", 0) or 0
        )

    venture_budget = min(
        float(payload.get("budget_usd", 10.0)),
        available_budget,
        10.0,
    )

    milestones = default_milestones()

    venture = {
        "id": venture_id,
        "project_id": project_id,
        "idea_id": idea_id,
        "name": name,
        "slug": venture_dir.name,
        "problem": problem,
        "solution": solution,
        "target_customer": target_customer,
        "opportunity_score": opportunity_score,
        "status": "active",
        "stage": "validation",
        "budget_usd": venture_budget,
        "revenue_usd": 0.0,
        "milestones": milestones,
        "assigned_agents": [
            "validation_agent",
            "builder_agent",
            "auditor_agent",
            "marketing_agent",
            "finance_agent",
        ],
        "workspace": str(venture_dir),
        "created_at": now(),
        "updated_at": now(),
    }

    created_files = create_workspace_files(
        venture_dir,
        venture,
    )

    project = {
        "id": project_id,
        "venture_id": venture_id,
        "idea_id": idea_id,
        "name": name,
        "status": "active",
        "stage": "validation",
        "assigned_agents": venture["assigned_agents"],
        "tasks": [
            {
                "name": milestone["name"],
                "owner": milestone["owner"],
                "status": milestone["status"],
            }
            for milestone in milestones
        ],
        "budget_usd": venture_budget,
        "revenue_usd": 0.0,
        "workspace": str(venture_dir),
        "created_at": now(),
        "updated_at": now(),
    }

    generated_tasks = [
        create_task(
            agent="validation_agent",
            action="validate_business_opportunity",
            project_id=project_id,
            payload={
                "venture_id": venture_id,
                "idea_id": idea_id,
                "project_name": name,
                "problem": problem,
                "target_customer": target_customer,
                "research_questions": [
                    "Who experiences this problem most often?",
                    "How are customers solving it now?",
                    "What evidence suggests willingness to pay?",
                    "Who are the main alternatives or competitors?",
                    "What is the smallest useful initial offer?",
                ],
            },
            priority=1,
        ),
        create_task(
            agent="builder_agent",
            action="build_prototype",
            project_id=project_id,
            payload={
                "venture_id": venture_id,
                "project_name": prototype_slug,
                "display_name": name,
                "problem": problem,
                "target_customer": target_customer,
                "solution": solution,
            },
            priority=2,
        ),
        create_task(
            agent="auditor_agent",
            action="audit_project",
            project_id=project_id,
            payload={
                "venture_id": venture_id,
                "project_slug": prototype_slug,
                "wait_for_builder": True,
            },
            priority=3,
        ),
        create_task(
            agent="marketing_agent",
            action="create_launch_plan",
            project_id=project_id,
            payload={
                "venture_id": venture_id,
                "project_slug": prototype_slug,
                "wait_for_audit": True,
            },
            priority=4,
        ),
        create_task(
            agent="finance_agent",
            action="financial_review",
            project_id=project_id,
            payload={
                "venture_id": venture_id,
                "requested_budget_usd": venture_budget,
            },
            priority=5,
        ),
    ]

    ventures.append(venture)
    projects.append(project)
    tasks.extend(generated_tasks)

    save_json(VENTURES_FILE, ventures)
    save_json(PROJECTS_FILE, projects)
    save_json(TASKS_FILE, tasks)

    idea["status"] = "incubating"
    idea["venture_id"] = venture_id
    idea["project_id"] = project_id
    idea["updated_at"] = now()

    save_json(IDEAS_FILE, ideas)

    state = {
        "last_incubation_at": now(),
        "active_ventures": len([
            item
            for item in ventures
            if str(item.get("status", "")).lower()
            == "active"
        ]),
        "total_ventures": len(ventures),
    }

    report = {
        "success": True,
        "status": "venture_created",
        "venture": venture,
        "project": project,
        "tasks_created": len(generated_tasks),
        "task_ids": [
            item["id"]
            for item in generated_tasks
        ],
        "files_created": created_files,
        "created_at": now(),
    }

    save_json(INCUBATOR_STATE_FILE, state)
    save_json(LATEST_REPORT_FILE, report)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_file = REPORT_DIR / (
        f"{venture_id}_incubation.json"
    )

    save_json(report_file, report)

    report["report_file"] = str(report_file)

    return report


def incubate_top_opportunity(
    task: dict[str, Any],
) -> dict[str, Any]:
    scores = normalize_list(load_json(SCORES_FILE, []))

    if not scores:
        return {
            "success": False,
            "error": "No opportunity scores are available",
        }

    ranked = sorted(
        scores,
        key=lambda item: float(
            item.get("final_score", 0) or 0
        ),
        reverse=True,
    )

    top = ranked[0]
    idea_id = str(top.get("idea_id", "")).strip()

    if not idea_id:
        return {
            "success": False,
            "error": "Top opportunity has no idea_id",
        }

    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    new_task = dict(task)
    new_task["payload"] = {
        **payload,
        "idea_id": idea_id,
    }

    return incubate_idea(new_task)


def list_ventures() -> dict[str, Any]:
    ventures = normalize_list(load_json(VENTURES_FILE, []))

    return {
        "success": True,
        "status": "ventures_listed",
        "count": len(ventures),
        "ventures": ventures,
    }


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action == "incubate_idea":
        return incubate_idea(task)

    if action == "incubate_top_opportunity":
        return incubate_top_opportunity(task)

    if action == "list_ventures":
        return list_ventures()

    return {
        "success": False,
        "error": f"Unsupported incubator action: {action}",
    }


if __name__ == "__main__":
    print(json.dumps(list_ventures(), indent=2))
