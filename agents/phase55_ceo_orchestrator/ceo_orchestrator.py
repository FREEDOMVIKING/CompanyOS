#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory/phase55"

STATE = MEMORY / "ceo_state.json"
RUNS = MEMORY / "ceo_runs.json"


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


def classify_next_action(action_class):
    autonomous = {
        "reversible_internal",
        "research",
        "analysis",
        "planning",
        "internal_build",
        "internal_test",
    }

    approval_required = {
        "financial_commitment",
        "irreversible_external",
    }

    if action_class in autonomous:
        return {
            "decision": "autonomous_continue",
            "approval_required": False,
        }

    if action_class in approval_required:
        return {
            "decision": "owner_approval_required",
            "approval_required": True,
        }

    return {
        "decision": "hold_for_review",
        "approval_required": True,
    }


def record_run(run):
    data = load_json(RUNS, {"runs": []})
    data.setdefault("runs", []).append(run)
    save_json(RUNS, data)

    state = {
        "last_run_at": run.get("completed_at"),
        "last_run_id": run.get("run_id"),
        "last_status": run.get("status"),
        "total_runs": len(data["runs"]),
    }

    save_json(STATE, state)


def finalize_ceo_cycle(
    objective,
    pipeline_results,
    proposed_next_action=None,
    action_class="reversible_internal",
):
    run_id = (
        "ceo-run-"
        + str(int(datetime.now(timezone.utc).timestamp() * 1000000))
    )

    decision = classify_next_action(action_class)

    run = {
        "run_id": run_id,
        "objective": objective,
        "status": "phase55_ceo_cycle_complete",
        "pipeline_results": pipeline_results,
        "proposed_next_action": proposed_next_action,
        "action_class": action_class,
        "decision": decision["decision"],
        "approval_required": decision["approval_required"],
        "completed_at": now(),
    }

    record_run(run)

    return {
        "success": True,
        **run,
    }


def status():
    runs = load_json(RUNS, {"runs": []})

    return {
        "success": True,
        "status": "phase55_ceo_orchestrator_status",
        "state": load_json(
            STATE,
            {
                "last_run_at": None,
                "last_run_id": None,
                "last_status": None,
                "total_runs": 0,
            },
        ),
        "run_count": len(runs.get("runs", [])),
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
