"""Convert researched opportunities into deterministic, observable work plans."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any


def _text(value: Any) -> str:
    return " ".join(str(value or "").split())


def _key(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _items(document: Any) -> list[dict[str, Any]]:
    if isinstance(document, list):
        return [item for item in document if isinstance(item, dict)]
    if isinstance(document, dict):
        values = document.get("opportunities", document.get("items", document))
        if isinstance(values, list):
            return [item for item in values if isinstance(item, dict)]
        if isinstance(values, dict):
            return [values]
    raise ValueError("input must be an opportunity object or a list of objects")


def _plan(opportunity: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    title = _text(opportunity.get("title") or opportunity.get("name"))
    problem = _text(opportunity.get("problem") or opportunity.get("need"))
    if not title or not problem:
        missing = "title" if not title else "problem"
        return None, [f"missing {missing}"]

    evidence = opportunity.get("evidence", [])
    if isinstance(evidence, str):
        evidence = [evidence]
    if not isinstance(evidence, list):
        evidence = []
    evidence = [_text(item) for item in evidence if _text(item)]
    owner = _text(opportunity.get("owner") or "unassigned")
    action = _text(opportunity.get("next_action") or opportunity.get("action"))
    if not action:
        action = f"Define and run a bounded test for: {title}"
    source = _text(opportunity.get("source") or "research")
    identity = _key({"title": title, "problem": problem, "source": source})
    work_id = f"opp-{identity}"

    steps = [
        {"id": "scope", "action": f"Write the smallest testable scope for {title}", "done_when": "scope, owner, and target are recorded"},
        {"id": "execute", "action": action, "done_when": "the stated action has a dated result"},
        {"id": "measure", "action": "Record baseline, result, and supporting evidence", "done_when": "result and evidence references are present"},
        {"id": "learn", "action": "Capture the next decision from the measured result", "done_when": "continue, revise, or close is explicitly recorded"},
    ]
    return {
        "work_id": work_id,
        "title": title,
        "problem": problem,
        "owner": owner,
        "source": source,
        "research_evidence": evidence,
        "status": "ready",
        "completion": {
            "required_steps": [step["id"] for step in steps],
            "evidence_required": True,
            "feedback_required": True,
        },
        "steps": steps,
        "feedback": {"result": None, "decision": None, "notes": []},
    }, []


def build_bridge(document: Any, strict: bool = False) -> dict[str, Any]:
    plans: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for index, opportunity in enumerate(_items(document)):
        plan, errors = _plan(opportunity)
        if plan:
            plans.append(plan)
        else:
            rejected.append({"index": index, "errors": errors})
    if strict and rejected:
        raise ValueError(f"invalid opportunities: {rejected}")
    return {
        "schema": "companyos.execution_plan.v1",
        "plans": plans,
        "rejected": rejected,
        "summary": {"received": len(plans) + len(rejected), "ready": len(plans), "rejected": len(rejected)},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="JSON file path, or - for stdin")
    parser.add_argument("--strict", action="store_true", help="fail when any opportunity is invalid")
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
        result = build_bridge(json.loads(raw), strict=args.strict)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
