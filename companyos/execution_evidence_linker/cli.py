"""Deterministically link execution evidence to work items and report completion."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _valid_time(value: Any) -> bool:
    if not value:
        return True
    try:
        datetime.fromisoformat(_text(value).replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def link_execution(payload: dict[str, Any]) -> dict[str, Any]:
    items = payload.get("work_items", [])
    evidence = payload.get("evidence", [])
    if not isinstance(items, list) or not isinstance(evidence, list):
        raise ValueError("work_items and evidence must be lists")

    by_work: dict[str, list[dict[str, Any]]] = {}
    issues: list[dict[str, str]] = []
    seen_evidence: set[str] = set()
    for record in evidence:
        if not isinstance(record, dict):
            issues.append({"kind": "invalid_evidence", "detail": "record is not an object"})
            continue
        evidence_id = _text(record.get("id"))
        work_id = _text(record.get("work_id"))
        if not evidence_id or not work_id:
            issues.append({"kind": "invalid_evidence", "detail": "id and work_id are required"})
            continue
        if evidence_id in seen_evidence:
            issues.append({"kind": "duplicate_evidence", "detail": evidence_id})
            continue
        seen_evidence.add(evidence_id)
        if not _valid_time(record.get("observed_at")):
            issues.append({"kind": "invalid_timestamp", "detail": evidence_id})
        by_work.setdefault(work_id, []).append(record)

    results: list[dict[str, Any]] = []
    complete = 0
    for item in items:
        if not isinstance(item, dict):
            issues.append({"kind": "invalid_work_item", "detail": "item is not an object"})
            continue
        work_id = _text(item.get("id"))
        required = item.get("required_evidence", [])
        if not work_id:
            issues.append({"kind": "invalid_work_item", "detail": "id is required"})
            continue
        if isinstance(required, str):
            required = [required]
        if not isinstance(required, list):
            required = []
            issues.append({"kind": "invalid_requirement", "detail": work_id})
        attached = by_work.get(work_id, [])
        types = {_text(row.get("type")) for row in attached}
        missing = sorted({_text(value) for value in required if _text(value)} - types)
        score = 1.0 if not required else (len(required) - len(missing)) / len(required)
        is_complete = not missing and bool(work_id)
        complete += int(is_complete)
        results.append({
            "id": work_id,
            "status": "complete" if is_complete else "blocked",
            "completion": round(score, 3),
            "missing_evidence": missing,
            "evidence_ids": sorted(_text(row.get("id")) for row in attached),
        })

    total = len(results)
    return {
        "schema": "execution_evidence_linker.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "work_items": results,
        "metrics": {
            "total": total,
            "complete": complete,
            "blocked": total - complete,
            "completion_rate": round(complete / total, 3) if total else 0.0,
            "evidence_records": len(seen_evidence),
            "issue_count": len(issues),
        },
        "issues": issues,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="JSON file; defaults to stdin")
    parser.add_argument("--output", help="write JSON result to a file")
    args = parser.parse_args(argv)
    try:
        raw = Path(args.input).read_text() if args.input else sys.stdin.read()
        result = link_execution(json.loads(raw))
        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            Path(args.output).write_text(rendered)
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
