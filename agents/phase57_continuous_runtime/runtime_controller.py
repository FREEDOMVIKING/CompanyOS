#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from pathlib import Path

from agents.phase56_autonomous_operations.operations_loop import (
    run_operations_cycle,
)

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory" / "phase57"
STATE_FILE = MEMORY / "runtime_state.json"

MEMORY.mkdir(parents=True, exist_ok=True)


def now():
    return datetime.now(timezone.utc).isoformat()


def default_state():
    return {
        "phase": 57,
        "status": "ready",
        "created_at": now(),
        "updated_at": now(),
        "runtime_cycles": 0,
        "successful_cycles": 0,
        "failed_cycles": 0,
        "consecutive_failures": 0,
        "last_cycle_at": None,
        "last_cycle_status": None,
        "last_error": None,
        "stop_requested": False,
        "history": [],
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


def run_runtime_cycle(
    objective,
    proposed_next_action="Continue internal validation and development",
    action_class="reversible_internal",
):
    state = load_state()

    if state.get("stop_requested"):
        return {
            "success": False,
            "status": "phase57_runtime_stopped",
            "runtime_state": state,
        }

    state["status"] = "running"
    state["runtime_cycles"] = state.get("runtime_cycles", 0) + 1
    state["last_cycle_at"] = now()
    save_state(state)

    try:
        result = run_operations_cycle(
            objective=objective,
            proposed_next_action=proposed_next_action,
            action_class=action_class,
        )

        success = bool(result.get("success"))

        if success:
            state["successful_cycles"] = state.get("successful_cycles", 0) + 1
            state["consecutive_failures"] = 0
            state["last_error"] = None
            state["last_cycle_status"] = "completed"
        else:
            state["failed_cycles"] = state.get("failed_cycles", 0) + 1
            state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
            state["last_cycle_status"] = "failed"

        state["status"] = "ready"

        state.setdefault("history", []).append({
            "cycle": state["runtime_cycles"],
            "objective": objective,
            "success": success,
            "completed_at": now(),
        })

        save_state(state)

        return {
            "success": success,
            "status": "phase57_runtime_cycle_complete",
            "operations_result": result,
            "runtime_state": state,
            "completed_at": now(),
        }

    except Exception as exc:
        state["status"] = "ready"
        state["failed_cycles"] = state.get("failed_cycles", 0) + 1
        state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
        state["last_cycle_status"] = "failed"
        state["last_error"] = str(exc)

        state.setdefault("history", []).append({
            "cycle": state["runtime_cycles"],
            "objective": objective,
            "success": False,
            "error": str(exc),
            "completed_at": now(),
        })

        save_state(state)

        return {
            "success": False,
            "status": "phase57_runtime_cycle_failed",
            "error": str(exc),
            "runtime_state": state,
            "completed_at": now(),
        }


def status():
    return {
        "success": True,
        "status": "phase57_continuous_runtime_status",
        "state": load_state(),
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
