#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from companyos.plugins.runtime import run_plugin

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE_DIR / "ceo_memory"

REPORT_DIR = MEMORY_DIR / "validation_reports"
SUMMARY_FILE = MEMORY_DIR / "validation_summary.json"
HISTORY_FILE = MEMORY_DIR / "validation_history.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")

    temporary.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    temporary.replace(path)


def unique_results(
    groups: list[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    output = []
    seen = set()

    for group in groups:
        for item in group:
            url = str(item.get("url", "")).strip()

            if not url or url in seen:
                continue

            seen.add(url)
            output.append(item)

    return output


def score_validation(
    evidence: list[dict[str, Any]],
    successful_queries: int,
) -> dict[str, Any]:
    domains = {
        urlparse(
            str(item.get("url", ""))
        ).netloc.lower()
        for item in evidence
        if item.get("url")
    }

    text = " ".join(
        (
            str(item.get("title", ""))
            + " "
            + str(item.get("snippet", ""))
        ).lower()
        for item in evidence
    )

    purchase_terms = [
        "buy",
        "pricing",
        "price",
        "subscription",
        "market",
        "customer",
        "demand",
        "sales",
    ]

    competitor_terms = [
        "software",
        "platform",
        "service",
        "template",
        "tool",
        "solution",
        "agency",
    ]

    purchase_hits = sum(
        text.count(term)
        for term in purchase_terms
    )

    competitor_hits = sum(
        text.count(term)
        for term in competitor_terms
    )

    evidence_score = min(len(evidence) / 2, 10)
    domain_score = min(len(domains), 10)
    demand_score = min(
        10,
        3
        + purchase_hits * 0.25
        + evidence_score * 0.35,
    )
    competition_score = min(
        10,
        2
        + competitor_hits * 0.15
        + domain_score * 0.25,
    )
    confidence = min(
        10,
        successful_queries * 2
        + min(len(evidence), 10) * 0.4,
    )

    validation_score = (
        demand_score * 0.45
        + confidence * 0.35
        + (10 - competition_score) * 0.20
    )

    return {
        "demand_score": round(demand_score, 2),
        "competition_score": round(
            competition_score,
            2,
        ),
        "confidence_score": round(confidence, 2),
        "validation_score": round(
            validation_score,
            2,
        ),
        "unique_domains": len(domains),
        "evidence_items": len(evidence),
    }


def validate_business_opportunity(
    task: dict[str, Any],
) -> dict[str, Any]:
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    name = str(
        payload.get(
            "project_name",
            payload.get("idea_name", "Unnamed opportunity"),
        )
    ).strip()

    problem = str(
        payload.get(
            "problem",
            "Customer problem requires research",
        )
    ).strip()

    customer = str(
        payload.get(
            "target_customer",
            "Potential customers",
        )
    ).strip()

    project_id = task.get("project_id")
    venture_id = payload.get("venture_id")
    idea_id = payload.get("idea_id")

    queries = [
        f"{customer} {problem} demand",
        f"{name} competitors pricing",
        f"{problem} software service alternatives",
    ]

    query_reports = []
    result_groups = []
    successful_queries = 0

    for query in queries:
        result = run_plugin(
            "web_research",
            {
                "action": "search_web",
                "payload": {
                    "query": query,
                    "maximum_results": 5,
                },
            },
        )

        query_reports.append({
            "query": query,
            "success": result.get("success") is True,
            "result_count": result.get(
                "result_count",
                0,
            ),
            "error": result.get("error"),
        })

        if result.get("success") is True:
            successful_queries += 1
            result_groups.append(
                result.get("results", [])
            )

    evidence = unique_results(result_groups)
    metrics = score_validation(
        evidence,
        successful_queries,
    )

    if metrics["validation_score"] >= 7:
        recommendation = "proceed_to_prototype"
    elif metrics["validation_score"] >= 5:
        recommendation = "continue_validation"
    else:
        recommendation = "deprioritize"

    report = {
        "success": bool(evidence),
        "status": (
            "business_validation_complete"
            if evidence
            else "business_validation_incomplete"
        ),
        "project_id": project_id,
        "venture_id": venture_id,
        "idea_id": idea_id,
        "name": name,
        "problem": problem,
        "target_customer": customer,
        "queries": query_reports,
        "metrics": metrics,
        "recommendation": recommendation,
        "evidence": evidence[:15],
        "validated_at": now(),
        "error": (
            None
            if evidence
            else (
                "No web evidence was collected. "
                "Check the phone's internet connection."
            )
        ),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    identity = (
        str(venture_id)
        if venture_id
        else str(project_id or idea_id or "validation")
    )

    report_file = (
        REPORT_DIR
        / f"{identity}_validation.json"
    )

    save_json(report_file, report)
    save_json(SUMMARY_FILE, report)

    history = load_json(HISTORY_FILE, [])

    if not isinstance(history, list):
        history = []

    history.append(report)
    save_json(HISTORY_FILE, history[-500:])

    report["report_file"] = str(report_file)

    return report


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action in {
        "validate_business_opportunity",
        "web_validate_idea",
    }:
        return validate_business_opportunity(task)

    return {
        "success": False,
        "error": f"Unsupported validation action: {action}",
    }


if __name__ == "__main__":
    print(json.dumps({
        "success": True,
        "status": "validation_agent_ready",
    }, indent=2))
