#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory/phase56"
STATE_FILE = MEMORY / "operations_state.json"

MEMORY.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def default_state():
    return {
        "phase": 56,
        "status": "ready",
        "created_at": now(),
        "updated_at": now(),
        "cycle_count": 0,
        "active_objective": None,
        "last_cycle_id": None,
        "last_cycle_status": None,
        "completed_objectives": [],
        "failed_objectives": [],
        "approval_queue": [],
        "cycle_history": []
    }


def load_state():
    if not STATE_FILE.exists():
        state = default_state()
        save_state(state)
        return state

    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        state = default_state()
        save_state(state)
        return state


def save_state(state):
    state["updated_at"] = now()
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return state


def begin_cycle(cycle_id, objective):
    state = load_state()

    state["status"] = "running"
    state["cycle_count"] = state.get("cycle_count", 0) + 1
    state["active_objective"] = objective
    state["last_cycle_id"] = cycle_id
    state["last_cycle_status"] = "running"

    state.setdefault("cycle_history", []).append({
        "cycle_id": cycle_id,
        "objective": objective,
        "started_at": now(),
        "status": "running"
    })

    return save_state(state)


def complete_cycle(cycle_id, result):
    state = load_state()

    success = bool(result.get("success"))

    state["status"] = "ready"
    state["last_cycle_status"] = "completed" if success else "failed"

    objective = state.get("active_objective")

    if success:
        state.setdefault("completed_objectives", []).append({
            "objective": objective,
            "cycle_id": cycle_id,
            "completed_at": now()
        })
    else:
        state.setdefault("failed_objectives", []).append({
            "objective": objective,
            "cycle_id": cycle_id,
            "failed_at": now()
        })

    for cycle in reversed(state.get("cycle_history", [])):
        if cycle.get("cycle_id") == cycle_id:
            cycle["status"] = state["last_cycle_status"]
            cycle["completed_at"] = now()
            break

    state["active_objective"] = None

    return save_state(state)


def status():
    return {
        "success": True,
        "status": "phase56_operations_state",
        "state": load_state()
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
