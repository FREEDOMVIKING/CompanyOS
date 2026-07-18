#!/usr/bin/env python3

import json
import random
from datetime import datetime, timezone
from pathlib import Path

MEMORY_DIR = Path("ceo_memory")

STATE_FILE = MEMORY_DIR / "company_state.json"
PROJECTS_FILE = MEMORY_DIR / "projects.json"
IDEAS_FILE = MEMORY_DIR / "ideas.json"
DECISIONS_FILE = MEMORY_DIR / "decisions.json"

ACTIONS = [
    "research_business_idea",
    "build_prototype",
    "test_project",
    "improve_project",
    "pause_weak_project",
    "review_company",
]


def load_json(path: Path, default):
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: Path, data) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    temporary.replace(path)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def choose_action(projects: list, ideas: list) -> str:
    active_projects = [
        project
        for project in projects
        if project.get("status") == "active"
    ]

    untested_projects = [
        project
        for project in active_projects
        if project.get("stage") == "prototype"
    ]

    if untested_projects:
        return "test_project"

    if not ideas:
        return "research_business_idea"

    if not active_projects:
        return "build_prototype"

    return random.choice([
        "improve_project",
        "review_company",
        "research_business_idea",
    ])


def create_business_idea(ideas: list) -> dict:
    categories = [
        "AI productivity tool",
        "local-service lead generator",
        "digital template business",
        "small-business automation service",
        "subscription analytics dashboard",
    ]

    idea = {
        "id": f"idea-{len(ideas) + 1}",
        "name": random.choice(categories),
        "status": "unvalidated",
        "problem": "To be researched",
        "target_customer": "To be researched",
        "revenue_model": "To be researched",
        "estimated_cost_usd": 0,
        "created_at": now(),
    }

    ideas.append(idea)
    return idea


def build_prototype(projects: list, ideas: list) -> dict | None:
    available_ideas = [
        idea for idea in ideas
        if idea.get("status") == "unvalidated"
    ]

    if not available_ideas:
        return None

    selected = available_ideas[0]
    selected["status"] = "selected"

    project = {
        "id": f"project-{len(projects) + 1}",
        "idea_id": selected["id"],
        "name": selected["name"],
        "status": "active",
        "stage": "prototype",
        "assigned_agents": [
            "research_agent",
            "builder_agent",
            "audit_agent",
        ],
        "tasks": [
            {
                "name": "Research customer problem",
                "owner": "research_agent",
                "status": "pending",
            },
            {
                "name": "Create minimum viable prototype",
                "owner": "builder_agent",
                "status": "pending",
            },
            {
                "name": "Validate prototype safety and quality",
                "owner": "audit_agent",
                "status": "pending",
            },
        ],
        "budget_usd": 0,
        "revenue_usd": 0,
        "created_at": now(),
        "updated_at": now(),
    }

    projects.append(project)
    return project


def execute_cycle() -> dict:
    state = load_json(STATE_FILE, {})
    projects = load_json(PROJECTS_FILE, [])
    ideas = load_json(IDEAS_FILE, [])
    decisions = load_json(DECISIONS_FILE, [])

    action = choose_action(projects, ideas)

    result = {
        "cycle_time": now(),
        "action": action,
        "status": "completed",
        "details": {},
    }

    if action == "research_business_idea":
        idea = create_business_idea(ideas)
        result["details"] = {
            "created_idea": idea,
        }

    elif action == "build_prototype":
        project = build_prototype(projects, ideas)

        if project:
            result["details"] = {
                "created_project": project,
            }
        else:
            result["status"] = "skipped"
            result["details"] = {
                "reason": "No unvalidated ideas available",
            }

    elif action == "test_project":
        project = next(
            (
                item for item in projects
                if item.get("stage") == "prototype"
                and item.get("status") == "active"
            ),
            None,
        )

        if project:
            project["stage"] = "testing"
            project["updated_at"] = now()
            result["details"] = {
                "project_id": project["id"],
                "message": "Project moved to testing",
            }
        else:
            result["status"] = "skipped"
            result["details"] = {
                "reason": "No prototype ready for testing",
            }

    else:
        result["details"] = {
            "message": f"{action} recorded for a future worker agent",
        }

    state["active_projects"] = len([
        project for project in projects
        if project.get("status") == "active"
    ])
    state["last_decision"] = result
    state["updated_at"] = now()

    decisions.append(result)

    save_json(STATE_FILE, state)
    save_json(PROJECTS_FILE, projects)
    save_json(IDEAS_FILE, ideas)
    save_json(DECISIONS_FILE, decisions)

    return result


if __name__ == "__main__":
    decision = execute_cycle()
    print(json.dumps(decision, indent=2))
