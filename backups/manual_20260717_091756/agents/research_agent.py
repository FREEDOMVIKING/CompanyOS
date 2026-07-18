#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE_DIR / "ceo_memory"
KNOWLEDGE_FILE = MEMORY_DIR / "knowledge.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    temporary.replace(path)


def build_report(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})
    idea_name = payload.get("idea_name", "Unnamed business idea")
    problem = payload.get("problem", "Problem not yet defined")
    target_customer = payload.get(
        "target_customer",
        "Small businesses and independent operators",
    )

    report = {
        "idea_name": idea_name,
        "problem": problem,
        "target_customer": target_customer,
        "market_hypothesis": (
            f"{target_customer} may pay for {idea_name} when it saves time, "
            "reduces repetitive work, or helps create revenue."
        ),
        "customer_questions": [
            "What task currently takes the most time?",
            "What tools are already being used?",
            "What does the current problem cost each month?",
            "Would the customer pay for a faster or automated solution?",
            "What would stop the customer from adopting it?",
        ],
        "validation_plan": [
            "Define one narrow customer problem.",
            "Create a simple landing-page description.",
            "Interview or survey at least five potential users.",
            "Measure interest before building a large product.",
            "Only move to development if demand is demonstrated.",
        ],
        "revenue_options": [
            "One-time purchase",
            "Monthly subscription",
            "Setup and customization fee",
            "Service package",
        ],
        "risk_factors": [
            "Demand may be weaker than expected",
            "The market may already have strong competitors",
            "Customer acquisition may cost more than projected",
            "The product may be too broad for an initial launch",
        ],
        "recommendation": "validate_before_building",
        "confidence_score": 0.55,
        "created_at": now(),
    }

    return report


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action != "research_business_idea":
        return {
            "success": False,
            "error": f"Unsupported research action: {action}",
        }

    report = build_report(task)

    knowledge = load_json(KNOWLEDGE_FILE, [])
    knowledge.append(
        {
            "type": "business_research",
            "task_id": task.get("id"),
            "project_id": task.get("project_id"),
            "report": report,
            "created_at": now(),
        }
    )
    save_json(KNOWLEDGE_FILE, knowledge)

    return {
        "success": True,
        "status": "research_complete",
        "report": report,
    }


if __name__ == "__main__":
    sample = {
        "id": "sample-task",
        "action": "research_business_idea",
        "payload": {
            "idea_name": "Local contractor lead organizer",
            "problem": "Small contractors lose track of incoming leads",
            "target_customer": "Small construction companies",
        },
    }

    print(json.dumps(run_task(sample), indent=2))
