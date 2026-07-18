#!/usr/bin/env python3

import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[3]
MEMORY_DIR = ROOT_DIR / "ceo_memory"


def load_json(name: str, default: Any) -> Any:
    try:
        return json.loads(
            (MEMORY_DIR / name).read_text(encoding="utf-8")
        )
    except Exception:
        return default


def normalize(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [
            item
            for item in value
            if isinstance(item, dict)
        ]

    return []


def health_check() -> dict[str, Any]:
    return {
        "success": MEMORY_DIR.exists(),
        "status": "healthy",
    }


def run(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    tasks = normalize(load_json("tasks.json", []))
    projects = normalize(load_json("projects.json", []))
    results = normalize(load_json("agent_results.json", []))

    if action == "company_metrics":
        completed = sum(
            1
            for item in tasks
            if str(item.get("status", "")).lower()
            in {"completed", "done", "successful", "success"}
        )

        failed = sum(
            1
            for item in tasks
            if str(item.get("status", "")).lower()
            in {"failed", "error", "rejected"}
        )

        return {
            "success": True,
            "status": "company_metrics_created",
            "metrics": {
                "projects": len(projects),
                "tasks": len(tasks),
                "completed_tasks": completed,
                "failed_tasks": failed,
                "stored_results": len(results),
            },
        }

    if action == "project_metrics":
        project_id = str(
            task.get("payload", {}).get("project_id", "")
        )

        related_tasks = [
            item
            for item in tasks
            if str(item.get("project_id", "")) == project_id
        ]

        return {
            "success": True,
            "status": "project_metrics_created",
            "project_id": project_id,
            "task_count": len(related_tasks),
        }

    if action == "task_metrics":
        return {
            "success": True,
            "status": "task_metrics_created",
            "total_tasks": len(tasks),
        }

    return {
        "success": False,
        "error": f"Unsupported metrics action: {action}",
    }
