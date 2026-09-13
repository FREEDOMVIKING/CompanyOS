"""Deterministic conversion of a researched opportunity into executable work."""
import argparse
import hashlib
import json
import sys
from typing import Any, Dict, List


def _text(value: Any, limit: int = 500) -> str:
    return " ".join(str(value or "").split())[:limit]


def _items(value: Any, limit: int = 8) -> List[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [_text(item, 300) for item in value if _text(item, 300)][:limit]


def _key(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def generate_plan(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(opportunity, dict):
        raise ValueError("opportunity must be a JSON object")
    title = _text(opportunity.get("title") or opportunity.get("name"), 160)
    objective = _text(opportunity.get("objective") or opportunity.get("problem"), 400)
    evidence = _items(opportunity.get("evidence") or opportunity.get("signals"))
    audience = _text(opportunity.get("customer") or opportunity.get("audience"), 180)
    if not title:
        raise ValueError("opportunity.title is required")
    if not objective:
        objective = "Clarify the customer outcome and test whether this opportunity merits further execution."
    if not evidence:
        evidence = ["No evidence supplied; capture evidence before treating the opportunity as validated."]

    seed = {"title": title, "objective": objective, "evidence": evidence, "audience": audience}
    plan_id = "opp-" + _key(seed)
    steps = [
        ("frame", "Frame the opportunity", "Write a one-sentence customer outcome and a falsifiable success condition."),
        ("verify", "Verify the signal", "Review the supplied evidence and record the strongest supporting observation and one disconfirming check."),
        ("test", "Run the smallest useful test", "Execute one reversible customer-facing test for the stated audience using the available operating process."),
        ("learn", "Capture the result", "Record reach, responses, completed actions, failure reasons, and the next evidence-backed decision."),
    ]
    tasks = []
    for index, (kind, name, action) in enumerate(steps, 1):
        task_seed = f"{plan_id}:{kind}:{index}"
        tasks.append({
            "id": "task-" + hashlib.sha256(task_seed.encode()).hexdigest()[:10],
            "sequence": index,
            "kind": kind,
            "name": name,
            "action": action,
            "inputs": {"opportunity": title, "objective": objective, "audience": audience, "evidence": evidence},
            "status": "pending",
            "completion": {"required": True, "result": None, "evidence": [], "failure_reason": None},
        })
    return {
        "plan_id": plan_id,
        "title": title,
        "objective": objective,
        "audience": audience,
        "source_evidence": evidence,
        "tasks": tasks,
        "metrics": {"total": len(tasks), "completed": 0, "blocked": 0, "completion_ratio": 0.0},
        "feedback": {"observations": [], "decision": None, "next_action": None},
    }


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", "-i", default="-", help="JSON file path, or - for stdin")
    args = parser.parse_args(argv)
    try:
        source = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
        payload = json.loads(source)
        result = generate_plan(payload)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
