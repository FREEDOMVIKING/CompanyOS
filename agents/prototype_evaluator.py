#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "prototype_evaluation_config.json"
REGISTRY = MEMORY / "prototype_registry.json"
EVALUATIONS = MEMORY / "prototype_evaluations.json"
HEALTH = MEMORY / "prototype_evaluation_health.json"
AUDIT = MEMORY / "prototype_evaluation_audit.json"
PLANS = MEMORY / "product_execution_plans.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT, [])
    if not isinstance(records, list):
        records = []
    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })
    save_json(AUDIT, records[-1000:])


def latest_prototype() -> dict[str, Any]:
    records = load_json(REGISTRY, {}).get("prototypes", [])
    if not records:
        raise RuntimeError("No prototype available")
    return records[-1]


def text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def file_score(directory: Path) -> tuple[int, list[str]]:
    checks = {
        "frontend/index.html": 10,
        "frontend/styles.css": 8,
        "frontend/app.js": 12,
        "server.py": 10,
        "README.md": 8,
    }

    score = 0
    notes = []

    for relative, points in checks.items():
        path = directory / relative
        if path.exists() and path.stat().st_size > 0:
            score += points
        else:
            notes.append(f"Missing or empty: {relative}")

    return score, notes


def content_score(directory: Path) -> tuple[int, list[str]]:
    html = text(directory / "frontend" / "index.html")
    css = text(directory / "frontend" / "styles.css")
    js = text(directory / "frontend" / "app.js")
    server = text(directory / "server.py")
    readme = text(directory / "README.md")

    score = 0
    notes = []

    checks = [
        ("Form present", "<form" in html, 6),
        ("Mobile viewport present", "viewport" in html, 5),
        ("Customer input present", "customer" in html.lower(), 5),
        ("Estimate input present", "amount" in html.lower(), 5),
        ("Bid status present", "status" in html.lower(), 4),
        ("Responsive CSS present", "@media" in css or "min(" in css, 4),
        ("Local storage used", "localStorage" in js, 6),
        ("Input validation present", "required" in html, 4),
        ("Local-only host", "127.0.0.1" in server, 5),
        ("README run instructions", "python server.py" in readme, 4),
    ]

    for label, passed, points in checks:
        if passed:
            score += points
        else:
            notes.append(f"Check failed: {label}")

    return score, notes


def safety_score(record: dict[str, Any]) -> tuple[int, list[str]]:
    fields = [
        "external_deployment_used",
        "external_publication_used",
        "external_spending_used",
    ]

    score = 0
    notes = []

    for field in fields:
        if record.get(field) is False:
            score += 4
        else:
            notes.append(f"Unsafe or unknown flag: {field}")

    return score, notes


def quality_score(directory: Path) -> tuple[int, list[str]]:
    js = text(directory / "frontend" / "app.js")
    html = text(directory / "frontend" / "index.html")

    score = 0
    notes = []

    if len(js) >= 500:
        score += 4
    else:
        notes.append("JavaScript implementation is very small")

    if len(html) >= 500:
        score += 3
    else:
        notes.append("HTML implementation is very small")

    if re.search(r"addEventListener", js):
        score += 3
    else:
        notes.append("No interactive event handling found")

    if "try" in js and "catch" in js:
        score += 2
    else:
        notes.append("No browser data error handling found")

    return score, notes


def recommendation(score: int, pass_score: int, ready_score: int) -> str:
    if score >= ready_score:
        return "release_ready"
    if score >= pass_score:
        return "passed"
    if score >= 55:
        return "needs_revision"
    return "failed"


def update_plan_status(project_id: str, decision: str, score: int) -> None:
    store = load_json(PLANS, {})
    for plan in store.get("plans", []):
        if str(plan.get("project_id")) != project_id:
            continue
        plan["prototype_evaluation_status"] = decision
        plan["prototype_evaluation_score"] = score
        plan["prototype_evaluated_at"] = now()
        plan["updated_at"] = now()
    save_json(PLANS, store)


def evaluate_latest() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {"success": False, "status": "prototype_evaluator_disabled"}
        audit("evaluate", result)
        return result

    prototype = latest_prototype()
    directory = Path(str(prototype.get("current_directory") or prototype.get("directory")))

    if not directory.exists():
        result = {
            "success": False,
            "status": "prototype_directory_missing",
            "directory": str(directory),
        }
        audit("evaluate", result)
        return result

    file_points, file_notes = file_score(directory)
    content_points, content_notes = content_score(directory)
    safety_points, safety_notes = safety_score(prototype)
    quality_points, quality_notes = quality_score(directory)

    total = file_points + content_points + safety_points + quality_points
    total = max(0, min(100, total))

    pass_score = int(config.get("minimum_pass_score", 75))
    ready_score = int(config.get("minimum_release_ready_score", 88))
    decision = recommendation(total, pass_score, ready_score)

    notes = file_notes + content_notes + safety_notes + quality_notes

    store = load_json(
        EVALUATIONS,
        {
            "schema_version": 1,
            "evaluations": [],
            "statistics": {},
        },
    )

    evaluation = {
        "id": f"evaluation-{prototype.get('id')}",
        "prototype_id": prototype.get("id"),
        "project_id": str(prototype.get("project_id")),
        "project_name": prototype.get("project_name"),
        "prototype_version": prototype.get("version"),
        "score": total,
        "decision": decision,
        "breakdown": {
            "file_structure": file_points,
            "content": content_points,
            "safety": safety_points,
            "quality": quality_points,
        },
        "notes": notes,
        "owner_release_approval_required": True,
        "automatic_revision": False,
        "automatic_release_approval": False,
        "automatic_external_deployment": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "evaluated_at": now(),
    }

    records = store.setdefault("evaluations", [])
    records[:] = [
        item for item in records
        if item.get("prototype_id") != prototype.get("id")
    ]
    records.append(evaluation)

    store["statistics"] = {
        "total": len(records),
        "passed": sum(1 for item in records if item.get("decision") == "passed"),
        "needs_revision": sum(
            1 for item in records if item.get("decision") == "needs_revision"
        ),
        "release_ready": sum(
            1 for item in records if item.get("decision") == "release_ready"
        ),
        "failed": sum(1 for item in records if item.get("decision") == "failed"),
    }
    store["last_updated_at"] = now()
    save_json(EVALUATIONS, store)

    update_plan_status(str(prototype.get("project_id")), decision, total)

    health = {
        "healthy": decision in {"passed", "release_ready"},
        "last_evaluated_at": now(),
        "latest_prototype_id": prototype.get("id"),
        "latest_score": total,
        "latest_decision": decision,
        "last_error": None,
    }
    save_json(HEALTH, health)

    result = {
        "success": True,
        "status": "prototype_evaluation_complete",
        "prototype_id": prototype.get("id"),
        "project_name": prototype.get("project_name"),
        "score": total,
        "decision": decision,
        "breakdown": evaluation["breakdown"],
        "notes": notes,
        "owner_release_approval_required": True,
        "automatic_revision": False,
        "automatic_external_deployment": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    audit("evaluate", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    store = load_json(EVALUATIONS, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "prototype_evaluation_status",
        "enabled": config.get("enabled", False),
        "automatic_evaluation": config.get("automatic_evaluation", False),
        "automatic_revision": config.get("automatic_revision", False),
        "automatic_release_approval": config.get(
            "automatic_release_approval", False
        ),
        "automatic_external_deployment": config.get(
            "automatic_external_deployment", False
        ),
        "automatic_publication": config.get("automatic_publication", False),
        "automatic_spending": config.get("automatic_spending", False),
        "statistics": store.get("statistics", {}),
        "health": health,
    }
    audit("status", result)
    return result


def latest() -> dict[str, Any]:
    records = load_json(EVALUATIONS, {}).get("evaluations", [])
    result = {
        "success": bool(records),
        "status": "latest_prototype_evaluation",
        "evaluation": records[-1] if records else None,
    }
    audit("latest", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "evaluate-latest":
            return print_result(evaluate_latest())
        if action == "status":
            return print_result(status())
        if action == "latest":
            return print_result(latest())

        return print_result({
            "success": False,
            "status": "unknown_evaluation_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "prototype_evaluation_error",
            "error": str(exc),
        }
        save_json(
            HEALTH,
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
