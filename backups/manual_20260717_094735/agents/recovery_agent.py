#!/usr/bin/env python3

import json
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE_DIR / "ceo_memory"

TASKS_FILE = MEMORY_DIR / "tasks.json"
RESULTS_FILE = MEMORY_DIR / "agent_results.json"
RECOVERY_FILE = MEMORY_DIR / "recovery_history.json"
ESCALATIONS_FILE = MEMORY_DIR / "escalations.json"

MAX_RETRIES = 3

RECOVERABLE_ERRORS = [
    "no module named",
    "module not found",
    "file not found",
    "does not exist",
    "timed out",
    "timeout",
    "connection",
    "temporary",
    "json",
    "permission denied",
    "resource temporarily unavailable",
]


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


def error_text(result: dict[str, Any]) -> str:
    inner = result.get("result", {})

    if not isinstance(inner, dict):
        inner = {}

    messages = [
        str(result.get("error", "")),
        str(result.get("stderr", "")),
        str(result.get("message", "")),
        str(inner.get("error", "")),
        str(inner.get("message", "")),
        str(inner.get("output", "")),
    ]

    return " ".join(
        message.strip()
        for message in messages
        if message and message.strip()
    )


def is_recoverable(message: str) -> bool:
    lowered = message.lower()

    return any(
        phrase in lowered
        for phrase in RECOVERABLE_ERRORS
    )


def find_task(
    tasks: list[dict[str, Any]],
    task_id: str,
) -> dict[str, Any] | None:
    return next(
        (
            task
            for task in tasks
            if str(task.get("id", "")) == task_id
        ),
        None,
    )


def retry_failed_tasks() -> dict[str, Any]:
    tasks = load_json(TASKS_FILE, [])
    results = load_json(RESULTS_FILE, [])
    recovery_history = load_json(RECOVERY_FILE, [])
    escalations = load_json(ESCALATIONS_FILE, [])

    if not isinstance(tasks, list):
        tasks = []

    if not isinstance(results, list):
        results = []

    if not isinstance(recovery_history, list):
        recovery_history = []

    if not isinstance(escalations, list):
        escalations = []

    retried = []
    escalated = []
    ignored = []

    failed_results = [
        result
        for result in results
        if isinstance(result, dict)
        and result.get("success") is False
        and not result.get("recovery_processed", False)
    ]

    for result in failed_results:
        task_id = str(result.get("task_id", "")).strip()
        message = error_text(result)

        task = find_task(tasks, task_id)

        if task is None:
            result["recovery_processed"] = True
            result["recovery_status"] = "task_not_found"

            ignored.append({
                "task_id": task_id,
                "reason": "Original task not found",
            })
            continue

        retries = int(task.get("retry_count", 0) or 0)

        if not is_recoverable(message):
            escalation = {
                "id": f"escalation-{uuid.uuid4().hex[:10]}",
                "task_id": task_id,
                "agent": task.get("agent"),
                "action": task.get("action"),
                "error": message or "Unknown unrecoverable error",
                "reason": "Error was not classified as recoverable",
                "status": "open",
                "created_at": now(),
            }

            escalations.append(escalation)
            escalated.append(escalation)

            result["recovery_processed"] = True
            result["recovery_status"] = "escalated"
            continue

        if retries >= MAX_RETRIES:
            escalation = {
                "id": f"escalation-{uuid.uuid4().hex[:10]}",
                "task_id": task_id,
                "agent": task.get("agent"),
                "action": task.get("action"),
                "error": message,
                "reason": f"Maximum retries reached: {MAX_RETRIES}",
                "status": "open",
                "created_at": now(),
            }

            escalations.append(escalation)
            escalated.append(escalation)

            result["recovery_processed"] = True
            result["recovery_status"] = "retry_limit_reached"
            continue

        retry_task = dict(task)
        retry_task["id"] = f"task-{uuid.uuid4().hex[:10]}"
        retry_task["status"] = "pending"
        retry_task["retry_count"] = retries + 1
        retry_task["retry_of"] = task.get("id")
        retry_task["created_at"] = now()
        retry_task["started_at"] = None
        retry_task["completed_at"] = None
        retry_task["last_error"] = message

        tasks.append(retry_task)

        recovery_entry = {
            "id": f"recovery-{uuid.uuid4().hex[:10]}",
            "original_task_id": task.get("id"),
            "retry_task_id": retry_task["id"],
            "agent": retry_task.get("agent"),
            "action": retry_task.get("action"),
            "retry_number": retry_task["retry_count"],
            "error": message,
            "status": "retry_queued",
            "created_at": now(),
        }

        recovery_history.append(recovery_entry)
        retried.append(recovery_entry)

        result["recovery_processed"] = True
        result["recovery_status"] = "retry_queued"
        result["retry_task_id"] = retry_task["id"]

    save_json(TASKS_FILE, tasks)
    save_json(RESULTS_FILE, results)
    save_json(RECOVERY_FILE, recovery_history[-500:])
    save_json(ESCALATIONS_FILE, escalations[-500:])

    return {
        "success": True,
        "status": "recovery_scan_complete",
        "failed_results_found": len(failed_results),
        "tasks_retried": len(retried),
        "tasks_escalated": len(escalated),
        "tasks_ignored": len(ignored),
        "retried": retried,
        "escalated": escalated,
        "ignored": ignored,
    }


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action == "recover_failed_tasks":
        return retry_failed_tasks()

    return {
        "success": False,
        "error": f"Unsupported recovery action: {action}",
    }


if __name__ == "__main__":
    try:
        print(json.dumps(retry_failed_tasks(), indent=2))
    except Exception:
        print(json.dumps({
            "success": False,
            "error": traceback.format_exc(),
        }, indent=2))
        raise
