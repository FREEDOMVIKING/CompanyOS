#!/usr/bin/env python3

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

CONFIG = ROOT / "ceo_memory/phase51/phase51_config.json"
PHASE50_OPPORTUNITIES = ROOT / "ceo_memory/phase50/opportunities.json"
PLANS = ROOT / "ceo_memory/phase51/execution_plans.json"
STATE = ROOT / "ceo_memory/phase51/phase51_state.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def make_plan_id(opportunity):
    seed = str(
        opportunity.get("opportunity_id")
        or opportunity.get("name")
        or now()
    )
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


def build_plan(opportunity):
    plan_id = make_plan_id(opportunity)

    name = opportunity.get("name", "Unnamed Opportunity")
    market = opportunity.get("market", "unknown")

    milestones = [
        {
            "id": "M1",
            "name": "Validate opportunity",
            "status": "pending"
        },
        {
            "id": "M2",
            "name": "Design solution and business model",
            "status": "pending"
        },
        {
            "id": "M3",
            "name": "Build minimum viable implementation",
            "status": "pending"
        },
        {
            "id": "M4",
            "name": "Validate market and revenue path",
            "status": "pending"
        },
        {
            "id": "M5",
            "name": "Prepare bounded launch",
            "status": "pending"
        }
    ]

    tasks = [
        {
            "task_id": f"{plan_id}-T1",
            "milestone": "M1",
            "title": "Analyze evidence and assumptions",
            "specialist_role": "research_agent",
            "depends_on": [],
            "action_class": "reversible_internal",
            "status": "pending"
        },
        {
            "task_id": f"{plan_id}-T2",
            "milestone": "M2",
            "title": "Create product and business architecture",
            "specialist_role": "strategy_agent",
            "depends_on": [f"{plan_id}-T1"],
            "action_class": "reversible_internal",
            "status": "pending"
        },
        {
            "task_id": f"{plan_id}-T3",
            "milestone": "M3",
            "title": "Build and test MVP",
            "specialist_role": "builder_agent",
            "depends_on": [f"{plan_id}-T2"],
            "action_class": "reversible_internal",
            "status": "pending"
        },
        {
            "task_id": f"{plan_id}-T4",
            "milestone": "M4",
            "title": "Validate customer and revenue path",
            "specialist_role": "growth_agent",
            "depends_on": [f"{plan_id}-T3"],
            "action_class": "reversible_internal",
            "status": "pending"
        },
        {
            "task_id": f"{plan_id}-T5",
            "milestone": "M5",
            "title": "Prepare launch decision package",
            "specialist_role": "ceo_agent",
            "depends_on": [f"{plan_id}-T4"],
            "action_class": "approval_boundary",
            "status": "pending"
        }
    ]

    return {
        "plan_id": plan_id,
        "opportunity_id": opportunity.get("opportunity_id"),
        "opportunity_name": name,
        "market": market,
        "qualification_score": opportunity.get("qualification_score", 0),
        "objective": f"Validate, build, and prepare a viable business execution path for {name}.",
        "milestones": milestones,
        "tasks": tasks,
        "risk_assessment": {
            "status": "required_before_external_execution",
            "financial_commitment_requires_owner_approval": True,
            "irreversible_external_action_requires_owner_approval": True
        },
        "execution_policy": {
            "autonomous_reversible_internal_actions": True,
            "financial_commitments": "owner_approval_required",
            "irreversible_external_actions": "owner_approval_required"
        },
        "status": "planned",
        "created_at": now()
    }


def generate():
    config = load_json(CONFIG, {})
    source = load_json(PHASE50_OPPORTUNITIES, {"opportunities": []})
    existing = load_json(PLANS, {"plans": []})

    minimum = config.get("minimum_opportunity_score", 65)
    max_active = config.get("max_active_plans", 10)

    existing_ids = {
        x.get("opportunity_id")
        for x in existing.get("plans", [])
        if x.get("opportunity_id")
    }

    created = []

    for opportunity in source.get("opportunities", []):
        if not opportunity.get("qualified", False):
            continue

        if float(opportunity.get("qualification_score", 0)) < minimum:
            continue

        if opportunity.get("opportunity_id") in existing_ids:
            continue

        if len(existing.get("plans", [])) >= max_active:
            break

        plan = build_plan(opportunity)
        existing.setdefault("plans", []).append(plan)
        existing_ids.add(opportunity.get("opportunity_id"))
        created.append(plan)

    save_json(PLANS, existing)

    state = {
        "last_run_at": now(),
        "plans_created": len(created),
        "total_plans": len(existing.get("plans", [])),
        "status": "ready"
    }

    save_json(STATE, state)

    return {
        "success": True,
        "status": "phase51_execution_plans_generated",
        "state": state,
        "created_plans": created
    }


def status():
    return {
        "success": True,
        "status": "phase51_execution_planner_status",
        "config": load_json(CONFIG, {}),
        "state": load_json(
            STATE,
            {
                "last_run_at": None,
                "plans_created": 0,
                "total_plans": 0,
                "status": "not_run"
            }
        ),
        "plans": load_json(PLANS, {"plans": []})
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
