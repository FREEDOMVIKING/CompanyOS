#!/usr/bin/env python3
"""Score researched opportunities for deterministic execution readiness.

Reads JSON from --input or stdin and emits a stable quality report. No external
services or credentials are required, making the result suitable for CI and
scheduled feedback loops.
"""
import argparse
import hashlib
import json
import sys
from typing import Any, Dict, Iterable, List


REQUIRED = ("problem", "customer", "evidence", "next_action", "owner", "acceptance")


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        return "; ".join(_text(item) for item in value if _text(item))
    return ""


def _items(payload: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(payload, dict):
        payload = payload.get("opportunities", payload.get("items", [payload]))
    if not isinstance(payload, list):
        raise ValueError("input must be an opportunity object or list")
    return (item for item in payload if isinstance(item, dict))


def _key(item: Dict[str, Any]) -> str:
    raw = json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def assess(item: Dict[str, Any]) -> Dict[str, Any]:
    fields = {name: _text(item.get(name)) for name in REQUIRED}
    missing = [name for name, value in fields.items() if not value]
    evidence = item.get("evidence")
    evidence_count = len(evidence) if isinstance(evidence, list) else (1 if fields["evidence"] else 0)
    acceptance_count = len(item.get("acceptance", [])) if isinstance(item.get("acceptance"), list) else int(bool(fields["acceptance"]))
    feedback = item.get("feedback")
    feedback_ready = isinstance(feedback, (dict, list)) and bool(feedback)
    score = sum(bool(value) for value in fields.values()) * 12
    score += min(evidence_count, 3) * 5
    score += min(acceptance_count, 3) * 4
    score += 5 if feedback_ready else 0
    score = min(score, 100)
    if missing:
        status = "needs_definition"
    elif score >= 80:
        status = "ready"
    elif score >= 60:
        status = "instrument"
    else:
        status = "needs_validation"
    next_step = (
        "execute against acceptance criteria" if status == "ready" else
        "add measurable feedback and outcome capture" if status == "instrument" else
        "add: " + ", ".join(missing or ["customer evidence"])
    )
    return {
        "id": str(item.get("id") or _key(item)),
        "title": _text(item.get("title") or item.get("name")) or "untitled opportunity",
        "score": score,
        "status": status,
        "missing": missing,
        "evidence_count": evidence_count,
        "acceptance_count": acceptance_count,
        "next_step": next_step,
    }


def report(payload: Any) -> Dict[str, Any]:
    assessed = [assess(item) for item in _items(payload)]
    assessed.sort(key=lambda row: (-row["score"], row["id"]))
    counts = {name: sum(row["status"] == name for row in assessed)
              for name in ("ready", "instrument", "needs_validation", "needs_definition")}
    return {
        "schema": "opportunity_quality.v1",
        "summary": {
            "total": len(assessed),
            "ready": counts["ready"],
            "execution_rate": round(counts["ready"] / len(assessed), 3) if assessed else 0.0,
            "status_counts": counts,
        },
        "opportunities": assessed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", default="-", help="JSON file path, or - for stdin")
    parser.add_argument("--pretty", action="store_true", help="indent JSON output")
    args = parser.parse_args()
    try:
        source = sys.stdin if args.input == "-" else open(args.input, encoding="utf-8")
        with source:
            payload = json.load(source)
        output = report(payload)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"schema": "opportunity_quality.v1", "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(output, sort_keys=True, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
