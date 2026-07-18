#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = BASE_DIR / "company_builds"
MARKETING_DIR = BASE_DIR / "ceo_memory" / "marketing"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_project_path(project_slug: str) -> Path:
    project_path = (BUILD_DIR / project_slug).resolve()
    build_root = BUILD_DIR.resolve()

    if project_path.parent != build_root:
        raise ValueError("Invalid project path")

    return project_path


def load_manifest(project_dir: Path) -> dict[str, Any]:
    manifest_path = project_dir / "manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError("Project manifest.json was not found")

    with manifest_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def create_launch_plan(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})
    project_slug = payload.get("project_slug", "").strip()

    if not project_slug:
        return {
            "success": False,
            "error": "project_slug is required",
        }

    try:
        project_dir = safe_project_path(project_slug)
        manifest = load_manifest(project_dir)
    except Exception as error:
        return {
            "success": False,
            "error": str(error),
        }

    project_name = manifest.get("project_name", project_slug)
    problem = manifest.get("problem", "Customer problem not defined")
    customer = manifest.get("target_customer", "Target customer not defined")
    solution = manifest.get("solution", "Solution not defined")

    launch_plan = {
        "project_slug": project_slug,
        "project_name": project_name,
        "target_customer": customer,
        "positioning": (
            f"{project_name} helps {customer} solve this problem: {problem}"
        ),
        "core_offer": solution,
        "headline": f"Make {problem.lower()} easier",
        "subheadline": (
            f"A practical solution designed for {customer.lower()}."
        ),
        "call_to_action": "Join the early-access list",
        "validation_channels": [
            "Direct customer outreach",
            "Relevant online communities",
            "Local business networking",
            "Simple landing-page signup test",
            "Short customer interviews",
        ],
        "launch_tasks": [
            {
                "name": "Create a one-page product description",
                "status": "pending",
            },
            {
                "name": "Prepare five customer interview questions",
                "status": "pending",
            },
            {
                "name": "Create an early-access offer",
                "status": "pending",
            },
            {
                "name": "Collect at least five responses",
                "status": "pending",
            },
            {
                "name": "Report interest and objections to the CEO",
                "status": "pending",
            },
        ],
        "success_metrics": {
            "minimum_customer_responses": 5,
            "minimum_interested_customers": 2,
            "minimum_interest_rate": 0.4,
            "maximum_initial_marketing_cost_usd": 0,
        },
        "draft_copy": {
            "short_description": (
                f"{project_name} is being built for {customer}. "
                f"It aims to solve: {problem}. "
                f"The proposed solution is: {solution}."
            ),
            "outreach_message": (
                f"Hi, I’m researching a tool for {customer.lower()} "
                f"that could help with {problem.lower()}. "
                "Would you be willing to answer five quick questions?"
            ),
        },
        "status": "draft",
        "created_at": now(),
    }

    MARKETING_DIR.mkdir(parents=True, exist_ok=True)
    output_file = MARKETING_DIR / f"{project_slug}_launch_plan.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(launch_plan, file, indent=2)

    markdown = f"""# {project_name} Launch Plan

## Target customer
{customer}

## Problem
{problem}

## Offer
{solution}

## Headline
{launch_plan["headline"]}

## Call to action
{launch_plan["call_to_action"]}

## Validation goal
Collect at least 5 customer responses and at least 2 expressions of interest.

## Outreach message
{launch_plan["draft_copy"]["outreach_message"]}
"""

    markdown_file = MARKETING_DIR / f"{project_slug}_launch_plan.md"
    markdown_file.write_text(markdown, encoding="utf-8")

    return {
        "success": True,
        "status": "launch_plan_created",
        "project_slug": project_slug,
        "launch_plan_file": str(output_file),
        "markdown_file": str(markdown_file),
        "launch_plan": launch_plan,
    }


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action != "create_launch_plan":
        return {
            "success": False,
            "error": f"Unsupported marketing action: {action}",
        }

    return create_launch_plan(task)


if __name__ == "__main__":
    sample_task = {
        "id": "sample-marketing-task",
        "action": "create_launch_plan",
        "project_id": "project-1",
        "payload": {
            "project_slug": "digital_template_business",
        },
    }

    print(json.dumps(run_task(sample_task), indent=2))
