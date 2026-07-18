#!/usr/bin/env python3

import json
import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE_DIR / "ceo_memory"

TASKS_FILE = MEMORY_DIR / "tasks.json"
RESULTS_FILE = MEMORY_DIR / "agent_results.json"
PROJECTS_FILE = MEMORY_DIR / "projects.json"
IDEAS_FILE = MEMORY_DIR / "ideas.json"
DECISIONS_FILE = MEMORY_DIR / "decisions.json"
RECOVERY_FILE = MEMORY_DIR / "recovery_history.json"
ESCALATIONS_FILE = MEMORY_DIR / "escalations.json"

LESSONS_FILE = MEMORY_DIR / "lessons.json"
AGENT_PERFORMANCE_FILE = MEMORY_DIR / "agent_performance.json"
LEARNING_STATE_FILE = MEMORY_DIR / "learning_state.json"
LATEST_REPORT_FILE = MEMORY_DIR / "learning_summary.json"
REPORT_DIR = MEMORY_DIR / "learning_reports"


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


def status_of(item: dict[str, Any]) -> str:
    return str(item.get("status", "unknown")).lower()


def result_success(result: dict[str, Any]) -> bool | None:
    top_level = result.get("success")

    if isinstance(top_level, bool):
        return top_level

    inner = result.get("result")

    if isinstance(inner, dict):
        inner_success = inner.get("success")

        if isinstance(inner_success, bool):
            return inner_success

    return None


def result_error(result: dict[str, Any]) -> str:
    parts: list[str] = []

    for key in ("error", "message", "stderr"):
        value = result.get(key)

        if value:
            parts.append(str(value))

    inner = result.get("result")

    if isinstance(inner, dict):
        for key in ("error", "message", "output"):
            value = inner.get(key)

            if value:
                parts.append(str(value))

    return " ".join(parts).strip()


def lesson_id(category: str, text: str) -> str:
    digest = hashlib.sha256(
        f"{category}:{text}".encode("utf-8")
    ).hexdigest()[:12]

    return f"lesson-{digest}"


def add_lesson(
    lessons: list[dict[str, Any]],
    category: str,
    text: str,
    source: str,
    confidence: float,
    related_agent: str | None = None,
    related_project: str | None = None,
) -> bool:
    identifier = lesson_id(category, text)

    existing = next(
        (
            lesson
            for lesson in lessons
            if lesson.get("id") == identifier
        ),
        None,
    )

    if existing:
        existing["observations"] = (
            int(existing.get("observations", 1)) + 1
        )
        existing["last_observed_at"] = now()
        existing["confidence"] = min(
            1.0,
            float(existing.get("confidence", confidence)) + 0.05,
        )
        return False

    lessons.append({
        "id": identifier,
        "category": category,
        "lesson": text,
        "source": source,
        "confidence": round(confidence, 2),
        "observations": 1,
        "related_agent": related_agent,
        "related_project": related_project,
        "created_at": now(),
        "last_observed_at": now(),
        "active": True,
    })

    return True


def calculate_agent_performance(
    tasks: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    task_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "pending_tasks": 0,
        }
    )

    result_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "total_results": 0,
            "successful_results": 0,
            "failed_results": 0,
        }
    )

    for task in tasks:
        agent = str(task.get("agent", "unknown_agent"))
        status = status_of(task)

        task_counts[agent]["total_tasks"] += 1

        if status in {
            "completed",
            "done",
            "success",
            "successful",
        }:
            task_counts[agent]["completed_tasks"] += 1
        elif status in {"failed", "error", "rejected"}:
            task_counts[agent]["failed_tasks"] += 1
        elif status in {"pending", "queued", "waiting", "running"}:
            task_counts[agent]["pending_tasks"] += 1

    for result in results:
        agent = str(result.get("agent", "unknown_agent"))
        success = result_success(result)

        result_counts[agent]["total_results"] += 1

        if success is True:
            result_counts[agent]["successful_results"] += 1
        elif success is False:
            result_counts[agent]["failed_results"] += 1

    all_agents = sorted(
        set(task_counts.keys()) | set(result_counts.keys())
    )

    performance: dict[str, Any] = {}

    for agent in all_agents:
        task_data = task_counts[agent]
        result_data = result_counts[agent]

        total_results = result_data["total_results"]
        successful = result_data["successful_results"]

        success_rate = (
            successful / total_results
            if total_results > 0
            else 0.0
        )

        if total_results == 0:
            rating = "unrated"
        elif success_rate >= 0.9:
            rating = "excellent"
        elif success_rate >= 0.7:
            rating = "good"
        elif success_rate >= 0.5:
            rating = "needs_improvement"
        else:
            rating = "poor"

        performance[agent] = {
            **task_data,
            **result_data,
            "success_rate": round(success_rate, 4),
            "rating": rating,
            "updated_at": now(),
        }

    return performance


def learn_from_results(
    lessons: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> int:
    created = 0

    for result in results:
        success = result_success(result)
        agent = str(result.get("agent", "unknown_agent"))
        action = str(result.get("action", "unknown_action"))
        project_id = result.get("project_id")

        if success is True:
            text = (
                f"{agent} successfully completed {action}; "
                "this workflow is currently operational."
            )

            if add_lesson(
                lessons,
                category="successful_workflow",
                text=text,
                source="agent_results",
                confidence=0.65,
                related_agent=agent,
                related_project=project_id,
            ):
                created += 1

        elif success is False:
            error = result_error(result) or "Unknown failure"

            text = (
                f"{agent} failed while performing {action}. "
                f"Observed issue: {error[:300]}"
            )

            if add_lesson(
                lessons,
                category="failure_pattern",
                text=text,
                source="agent_results",
                confidence=0.75,
                related_agent=agent,
                related_project=project_id,
            ):
                created += 1

    return created


def learn_from_projects(
    lessons: list[dict[str, Any]],
    projects: list[dict[str, Any]],
) -> int:
    created = 0

    for project in projects:
        project_id = str(project.get("id", "unknown_project"))
        name = str(project.get("name", project_id))
        status = status_of(project)
        stage = str(project.get("stage", "unknown"))

        if status in {"completed", "profitable", "validated"}:
            text = (
                f"Project '{name}' reached {status} status "
                f"from stage '{stage}'."
            )

            if add_lesson(
                lessons,
                category="project_success",
                text=text,
                source="projects",
                confidence=0.85,
                related_project=project_id,
            ):
                created += 1

        elif status in {"failed", "cancelled", "rejected"}:
            text = (
                f"Project '{name}' ended with status '{status}' "
                f"at stage '{stage}'. Review its decisions before "
                "starting a similar project."
            )

            if add_lesson(
                lessons,
                category="project_failure",
                text=text,
                source="projects",
                confidence=0.85,
                related_project=project_id,
            ):
                created += 1

    return created


def learn_from_recovery(
    lessons: list[dict[str, Any]],
    recoveries: list[dict[str, Any]],
) -> int:
    created = 0

    for recovery in recoveries:
        agent = str(recovery.get("agent", "unknown_agent"))
        action = str(recovery.get("action", "unknown_action"))
        error = str(recovery.get("error", "Unknown error"))
        retry_number = recovery.get("retry_number", 1)

        text = (
            f"{agent} required retry {retry_number} for {action}. "
            f"Original issue: {error[:300]}"
        )

        if add_lesson(
            lessons,
            category="recovery_pattern",
            text=text,
            source="recovery_history",
            confidence=0.7,
            related_agent=agent,
        ):
            created += 1

    return created


def learn_from_escalations(
    lessons: list[dict[str, Any]],
    escalations: list[dict[str, Any]],
) -> int:
    created = 0

    for escalation in escalations:
        agent = str(escalation.get("agent", "unknown_agent"))
        action = str(escalation.get("action", "unknown_action"))
        reason = str(escalation.get("reason", "Unknown reason"))

        text = (
            f"{agent} escalation for {action}: {reason}. "
            "Human or executive review may be required."
        )

        if add_lesson(
            lessons,
            category="escalation_pattern",
            text=text,
            source="escalations",
            confidence=0.9,
            related_agent=agent,
        ):
            created += 1

    return created


def create_recommendations(
    performance: dict[str, Any],
    lessons: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []

    for agent, data in performance.items():
        success_rate = float(data.get("success_rate", 0))
        total_results = int(data.get("total_results", 0))

        if total_results >= 2 and success_rate < 0.5:
            recommendations.append({
                "priority": "high",
                "type": "agent_review",
                "agent": agent,
                "recommendation": (
                    f"Review {agent}; its recorded success rate is "
                    f"{success_rate:.0%}."
                ),
            })

        elif total_results >= 3 and success_rate >= 0.9:
            recommendations.append({
                "priority": "normal",
                "type": "agent_strength",
                "agent": agent,
                "recommendation": (
                    f"{agent} is performing reliably and may handle "
                    "more work in its current area."
                ),
            })

    failure_lessons = [
        lesson
        for lesson in lessons
        if lesson.get("category") in {
            "failure_pattern",
            "project_failure",
            "escalation_pattern",
        }
        and lesson.get("active", True)
    ]

    repeated_failures = [
        lesson
        for lesson in failure_lessons
        if int(lesson.get("observations", 1)) >= 2
    ]

    if repeated_failures:
        recommendations.append({
            "priority": "high",
            "type": "repeated_failure",
            "count": len(repeated_failures),
            "recommendation": (
                "Review repeated failure lessons before creating "
                "new related tasks."
            ),
        })

    if not recommendations:
        recommendations.append({
            "priority": "normal",
            "type": "continue_learning",
            "recommendation": (
                "No major learning risks detected. Continue collecting "
                "results and project outcomes."
            ),
        })

    return recommendations


def run_learning_cycle() -> dict[str, Any]:
    tasks = normalize_list(load_json(TASKS_FILE, []))
    results = normalize_list(load_json(RESULTS_FILE, []))
    projects = normalize_list(load_json(PROJECTS_FILE, []))
    ideas = normalize_list(load_json(IDEAS_FILE, []))
    decisions = normalize_list(load_json(DECISIONS_FILE, []))
    recoveries = normalize_list(load_json(RECOVERY_FILE, []))
    escalations = normalize_list(load_json(ESCALATIONS_FILE, []))
    lessons = normalize_list(load_json(LESSONS_FILE, []))

    lessons_created = 0

    lessons_created += learn_from_results(lessons, results)
    lessons_created += learn_from_projects(lessons, projects)
    lessons_created += learn_from_recovery(lessons, recoveries)
    lessons_created += learn_from_escalations(
        lessons,
        escalations,
    )

    lessons = lessons[-2000:]

    performance = calculate_agent_performance(tasks, results)

    recommendations = create_recommendations(
        performance,
        lessons,
    )

    state = {
        "last_learning_cycle_at": now(),
        "total_lessons": len(lessons),
        "active_lessons": len([
            lesson
            for lesson in lessons
            if lesson.get("active", True)
        ]),
        "agents_analyzed": len(performance),
        "tasks_analyzed": len(tasks),
        "results_analyzed": len(results),
        "projects_analyzed": len(projects),
        "ideas_analyzed": len(ideas),
        "decisions_analyzed": len(decisions),
        "recoveries_analyzed": len(recoveries),
        "escalations_analyzed": len(escalations),
    }

    summary = {
        "success": True,
        "status": "learning_cycle_complete",
        "completed_at": now(),
        "new_lessons_created": lessons_created,
        "total_lessons": len(lessons),
        "agent_performance": performance,
        "recommendations": recommendations,
        "learning_state": state,
    }

    save_json(LESSONS_FILE, lessons)
    save_json(AGENT_PERFORMANCE_FILE, performance)
    save_json(LEARNING_STATE_FILE, state)
    save_json(LATEST_REPORT_FILE, summary)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_file = REPORT_DIR / (
        "learning_report_"
        + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        + ".json"
    )

    save_json(report_file, summary)

    summary["report_file"] = str(report_file)

    return summary


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action in {
        "learn",
        "learning_cycle",
        "analyze_company_history",
    }:
        return run_learning_cycle()

    return {
        "success": False,
        "error": f"Unsupported learning action: {action}",
    }


if __name__ == "__main__":
    print(json.dumps(run_learning_cycle(), indent=2))
