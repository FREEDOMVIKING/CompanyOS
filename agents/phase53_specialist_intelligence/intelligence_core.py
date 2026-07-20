#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory/phase53"
STATE = MEMORY / "intelligence_state.json"
ARTIFACTS = MEMORY / "artifacts.json"


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


ROLE_CAPABILITIES = {
    "research_agent": [
        "evidence_analysis",
        "assumption_detection",
        "market_research",
        "risk_discovery",
        "information_gaps"
    ],
    "strategy_agent": [
        "business_strategy",
        "product_strategy",
        "competitive_positioning",
        "prioritization",
        "execution_planning"
    ],
    "builder_agent": [
        "technical_architecture",
        "implementation_planning",
        "testing_strategy",
        "deliverable_creation",
        "system_design"
    ],
    "growth_agent": [
        "customer_acquisition",
        "pricing",
        "revenue_strategy",
        "market_validation",
        "growth_experiments"
    ],
    "ceo_agent": [
        "result_synthesis",
        "decision_analysis",
        "resource_prioritization",
        "risk_review",
        "executive_recommendation"
    ]
}


def analyze(role, task, context=None):
    context = context or {}

    if role not in ROLE_CAPABILITIES:
        return {
            "success": False,
            "status": "phase53_unknown_specialist",
            "role": role
        }

    prior_results = context.get("prior_results", [])

    artifact = {
        "artifact_id": f"{role}-{int(datetime.now(timezone.utc).timestamp() * 1000000)}",
        "created_at": now(),
        "role": role,
        "task": task,
        "capabilities_used": ROLE_CAPABILITIES[role],
        "analysis": {
            "objective": task,
            "context_available": bool(context),
            "prior_results_available": len(prior_results),
            "findings": [],
            "recommendations": [],
            "risks": [],
            "assumptions": [],
            "next_inputs": []
        }
    }

    if prior_results:
        artifact["analysis"]["findings"].append(
            f"Received {len(prior_results)} prior specialist result(s) for synthesis."
        )

    artifact["analysis"]["recommendations"].append(
        f"Continue {role} analysis using validated evidence and downstream specialist context."
    )

    artifact["analysis"]["risks"].append(
        "Conclusions should remain bounded by available evidence and execution permissions."
    )

    stored = load_json(ARTIFACTS, {"artifacts": []})
    stored.setdefault("artifacts", []).append(artifact)
    save_json(ARTIFACTS, stored)

    state = {
        "last_run_at": now(),
        "last_role": role,
        "last_task": task,
        "total_artifacts": len(stored["artifacts"])
    }

    save_json(STATE, state)

    return {
        "success": True,
        "status": "phase53_intelligence_complete",
        "artifact": artifact
    }


def status():
    return {
        "success": True,
        "status": "phase53_intelligence_status",
        "state": load_json(
            STATE,
            {
                "last_run_at": None,
                "last_role": None,
                "last_task": None,
                "total_artifacts": 0
            }
        ),
        "artifacts": load_json(ARTIFACTS, {"artifacts": []})
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
