#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime, timezone

from agents.phase53_specialist_intelligence.intelligence_core import analyze as phase53_analyze

ROOT = Path(__file__).resolve().parents[2]

STATE = ROOT / "ceo_memory/phase52/runtime_state.json"
RESULTS = ROOT / "ceo_memory/phase52/specialist_results.json"


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


def run_specialist(role, task, context=None):
    context = context or {}

    role_prompts = {
        "research_agent": (
            "Analyze evidence, assumptions, market context, risks, "
            "and unanswered questions."
        ),
        "strategy_agent": (
            "Turn validated findings into a practical business, product, "
            "and execution strategy."
        ),
        "builder_agent": (
            "Design implementation steps, technical architecture, "
            "testing requirements, and deliverables."
        ),
        "growth_agent": (
            "Develop customer acquisition, positioning, validation, "
            "pricing, and revenue strategy."
        ),
        "ceo_agent": (
            "Synthesize specialist results into an executive decision package."
        )
    }

    if role not in role_prompts:
        return {
            "success": False,
            "status": "phase52_unknown_specialist",
            "role": role
        }

    phase53_result = phase53_analyze(
        role=role,
        task=task,
        context=context
    )

    if not phase53_result.get("success", False):
        return {
            "success": False,
            "status": "phase52_phase53_execution_failed",
            "role": role,
            "task": task,
            "phase53_result": phase53_result
        }

    artifact = phase53_result.get("artifact", {})
    analysis = artifact.get("analysis", {})

    result = {
        "success": True,
        "status": "phase52_specialist_complete",
        "role": role,
        "task": task,
        "mission": role_prompts[role],
        "context_received": context,
        "output": {
            "summary": f"{role} completed Phase 53 intelligence analysis for: {task}",
            "findings": analysis.get("findings", []),
            "recommendations": analysis.get("recommendations", []),
            "risks": analysis.get("risks", []),
            "assumptions": analysis.get("assumptions", []),
            "next_inputs": analysis.get("next_inputs", [])
        },
        "phase53_artifact": artifact,
        "completed_at": now()
    }

    stored = load_json(RESULTS, {"results": []})
    stored.setdefault("results", []).append(result)
    save_json(RESULTS, stored)

    state = {
        "last_run_at": now(),
        "last_role": role,
        "total_results": len(stored.get("results", []))
    }

    save_json(STATE, state)

    return result


def status():
    return {
        "success": True,
        "status": "phase52_specialist_runtime_status",
        "state": load_json(
            STATE,
            {
                "last_run_at": None,
                "last_role": None,
                "total_results": 0
            }
        ),
        "results": load_json(RESULTS, {"results": []})
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
