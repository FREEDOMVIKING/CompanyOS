"""Deterministic integrity checks for opportunity-to-execution work items."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from typing import Any, Iterable, Mapping

STATUSES = frozenset({"backlog", "ready", "in_progress", "blocked", "done"})
REQUIRED = ("id", "title", "status")


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _issue(item_id: Any, code: str, message: str) -> dict[str, str]:
    return {"id": str(item_id or "<missing>"), "code": code, "message": message}


def validate_work_items(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate work items without mutating them and return an auditable report."""
    issues: list[dict[str, str]] = []
    seen: set[str] = set()
    total = 0
    completed = 0

    for position, raw in enumerate(items):
        total += 1
        item = raw if isinstance(raw, Mapping) else {}
        item_id = item.get("id")
        display_id = item_id or f"row-{position + 1}"
        if not isinstance(raw, Mapping):
            issues.append(_issue(display_id, "not_mapping", "work item must be an object"))
            continue
        missing = [field for field in REQUIRED if not item.get(field)]
        for field in missing:
            issues.append(_issue(display_id, "missing_field", f"missing required field: {field}"))
        key = str(item_id) if item_id is not None else ""
        if key and key in seen:
            issues.append(_issue(display_id, "duplicate_id", "work item id is not unique"))
        if key:
            seen.add(key)

        status = item.get("status")
        if status not in STATUSES:
            issues.append(_issue(display_id, "invalid_status", f"status must be one of {sorted(STATUSES)}"))
        if status == "in_progress" and not item.get("owner"):
            issues.append(_issue(display_id, "missing_owner", "in-progress work requires an owner"))
        if status == "done":
            completed += 1
            if not item.get("completed_at"):
                issues.append(_issue(display_id, "missing_completion_time", "done work requires completed_at"))
            if not item.get("outcome") and not item.get("feedback"):
                issues.append(_issue(display_id, "missing_feedback", "done work requires outcome or feedback"))

        progress = item.get("progress", 0 if status != "done" else 1)
        if not isinstance(progress, (int, float)) or isinstance(progress, bool) or not 0 <= progress <= 1:
            issues.append(_issue(display_id, "invalid_progress", "progress must be a number from 0 to 1"))
        elif status == "done" and progress < 1:
            issues.append(_issue(display_id, "incomplete_done", "done work must have progress=1"))

        created = _timestamp(item.get("created_at"))
        finished = _timestamp(item.get("completed_at"))
        if item.get("created_at") and created is None:
            issues.append(_issue(display_id, "invalid_created_at", "created_at must be ISO-8601"))
        if item.get("completed_at") and finished is None:
            issues.append(_issue(display_id, "invalid_completed_at", "completed_at must be ISO-8601"))
        if created and finished and finished < created:
            issues.append(_issue(display_id, "reversed_timestamps", "completed_at precedes created_at"))

    ordered_issues = sorted(issues, key=lambda issue: (issue["id"], issue["code"], issue["message"]))
    valid = not ordered_issues
    summary = {
        "items": total,
        "completed": completed,
        "completion_rate": round(completed / total, 4) if total else 0.0,
        "issue_count": len(ordered_issues),
        "valid": valid,
    }
    fingerprint = hashlib.sha256(
        json.dumps({"summary": summary, "issues": ordered_issues}, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]
    return {"valid": valid, "summary": summary, "issues": ordered_issues, "fingerprint": fingerprint}


def check_integrity(items: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Compatibility alias for callers that use a check-oriented name."""
    return validate_work_items(items)

# Legacy compatibility names retained for older phase tests/importers.
# They delegate to the current deterministic validation implementation.
class DataIntegrityGuard:
    @staticmethod
    def validate(items):
        return validate_work_items(items)

    @staticmethod
    def check(items):
        return check_integrity(items)


def data_integrity(items):
    return validate_work_items(items)
