#!/usr/bin/env python3

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PHASE51_RESULTS = ROOT / "ceo_memory/phase51/task_results.json"
PHASE51_PLANS = ROOT / "ceo_memory/phase51/execution_plans.json"


def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def build_context(plan_id, task_id):
    plans = load_json(PHASE51_PLANS, {"plans": []})
    results = load_json(PHASE51_RESULTS, {"results": []})

    plan = None

    for item in plans.get("plans", []):
        if item.get("plan_id") == plan_id:
            plan = item
            break

    prior_results = []

    for result in results.get("results", []):
        if result.get("plan_id") == plan_id:
            prior_results.append(result)

    return {
        "plan": plan,
        "current_task_id": task_id,
        "prior_results": prior_results
    }


def status():
    plans = load_json(PHASE51_PLANS, {"plans": []})
    results = load_json(PHASE51_RESULTS, {"results": []})

    return {
        "success": True,
        "status": "phase52_context_bridge_status",
        "plans_available": len(plans.get("plans", [])),
        "prior_results_available": len(results.get("results", []))
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
