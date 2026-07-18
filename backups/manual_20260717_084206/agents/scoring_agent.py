#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE_DIR / "ceo_memory"

IDEAS_FILE = MEMORY_DIR / "ideas.json"
PROJECTS_FILE = MEMORY_DIR / "projects.json"
LESSONS_FILE = MEMORY_DIR / "lessons.json"

SCORES_FILE = MEMORY_DIR / "opportunity_scores.json"
LATEST_FILE = MEMORY_DIR / "scoring_summary.json"
REPORT_DIR = MEMORY_DIR / "scoring_reports"

WEIGHTS = {
    "demand": 0.22,
    "revenue_potential": 0.18,
    "automation_potential": 0.15,
    "speed_to_launch": 0.12,
    "confidence": 0.10,
    "startup_cost": 0.10,
    "competition": 0.07,
    "risk": 0.06,
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


def clamp(value: float) -> float:
    return max(0.0, min(10.0, value))


def numeric(
    item: dict[str, Any],
    key: str,
    default: float,
) -> float:
    try:
        return clamp(float(item.get(key, default)))
    except (TypeError, ValueError):
        return default


def infer_metrics(
    idea: dict[str, Any],
) -> dict[str, float]:
    name = str(idea.get("name", "")).lower()
    description = " ".join([
        str(idea.get("description", "")),
        str(idea.get("problem", "")),
        str(idea.get("solution", "")),
        str(idea.get("target_customer", "")),
    ]).lower()

    text = f"{name} {description}"

    metrics = {
        "demand": numeric(idea, "demand_score", 5.5),
        "revenue_potential": numeric(
            idea,
            "revenue_potential_score",
            5.0,
        ),
        "automation_potential": numeric(
            idea,
            "automation_potential_score",
            6.0,
        ),
        "speed_to_launch": numeric(
            idea,
            "speed_to_launch_score",
            6.0,
        ),
        "confidence": numeric(
            idea,
            "confidence_score",
            5.0,
        ),
        "startup_cost": numeric(
            idea,
            "startup_cost_score",
            7.0,
        ),
        "competition": numeric(
            idea,
            "competition_score",
            5.0,
        ),
        "risk": numeric(
            idea,
            "risk_score",
            6.0,
        ),
    }

    low_cost_terms = [
        "template",
        "digital",
        "newsletter",
        "directory",
        "content",
        "software",
        "saas",
        "automation",
        "consulting",
        "service",
    ]

    high_automation_terms = [
        "ai",
        "automation",
        "digital",
        "software",
        "template",
        "report",
        "generator",
        "monitor",
    ]

    fast_launch_terms = [
        "template",
        "newsletter",
        "directory",
        "service",
        "consulting",
        "digital product",
    ]

    high_risk_terms = [
        "trading",
        "crypto",
        "medical",
        "legal",
        "financial",
        "investment",
        "gambling",
    ]

    if any(term in text for term in low_cost_terms):
        metrics["startup_cost"] += 1.0

    if any(term in text for term in high_automation_terms):
        metrics["automation_potential"] += 1.0

    if any(term in text for term in fast_launch_terms):
        metrics["speed_to_launch"] += 1.0

    if any(term in text for term in high_risk_terms):
        metrics["risk"] -= 2.0
        metrics["confidence"] -= 0.5

    return {
        key: clamp(value)
        for key, value in metrics.items()
    }


def score_idea(
    idea: dict[str, Any],
    lessons: list[dict[str, Any]],
) -> dict[str, Any]:
    metrics = infer_metrics(idea)

    score = sum(
        metrics[name] * weight
        for name, weight in WEIGHTS.items()
    )

    idea_name = str(
        idea.get("name", idea.get("id", "Unnamed idea"))
    )

    related_failure_lessons = [
        lesson
        for lesson in lessons
        if lesson.get("active", True)
        and lesson.get("category") in {
            "failure_pattern",
            "project_failure",
            "escalation_pattern",
        }
        and any(
            word in str(lesson.get("lesson", "")).lower()
            for word in idea_name.lower().split()
            if len(word) >= 4
        )
    ]

    penalty = min(len(related_failure_lessons) * 0.25, 1.5)
    final_score = max(0.0, score - penalty)

    if final_score >= 8.0:
        rating = "excellent"
        recommendation = "prioritize"
    elif final_score >= 6.5:
        rating = "strong"
        recommendation = "validate"
    elif final_score >= 5.0:
        rating = "moderate"
        recommendation = "research_more"
    elif final_score >= 3.5:
        rating = "weak"
        recommendation = "deprioritize"
    else:
        rating = "poor"
        recommendation = "reject"

    return {
        "idea_id": idea.get("id"),
        "name": idea_name,
        "status": idea.get("status"),
        "metrics": {
            key: round(value, 2)
            for key, value in metrics.items()
        },
        "raw_score": round(score, 3),
        "failure_penalty": round(penalty, 3),
        "final_score": round(final_score, 3),
        "rating": rating,
        "recommendation": recommendation,
        "scored_at": now(),
    }


def run_scoring_cycle() -> dict[str, Any]:
    ideas = normalize_list(load_json(IDEAS_FILE, []))
    projects = normalize_list(load_json(PROJECTS_FILE, []))
    lessons = normalize_list(load_json(LESSONS_FILE, []))

    scores = [
        score_idea(idea, lessons)
        for idea in ideas
    ]

    scores.sort(
        key=lambda item: item["final_score"],
        reverse=True,
    )

    for rank, item in enumerate(scores, start=1):
        item["rank"] = rank

    top_opportunity = scores[0] if scores else None

    summary = {
        "success": True,
        "status": "scoring_cycle_complete",
        "completed_at": now(),
        "ideas_scored": len(scores),
        "projects_reviewed": len(projects),
        "top_opportunity": top_opportunity,
        "rankings": scores,
        "weights": WEIGHTS,
    }

    save_json(SCORES_FILE, scores)
    save_json(LATEST_FILE, summary)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_file = REPORT_DIR / (
        "scoring_report_"
        + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        + ".json"
    )

    save_json(report_file, summary)

    summary["report_file"] = str(report_file)

    return summary


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action in {
        "score_ideas",
        "scoring_cycle",
        "rank_opportunities",
    }:
        return run_scoring_cycle()

    return {
        "success": False,
        "error": f"Unsupported scoring action: {action}",
    }


if __name__ == "__main__":
    print(json.dumps(run_scoring_cycle(), indent=2))
