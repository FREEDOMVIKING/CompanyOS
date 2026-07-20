#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime, timezone

from agents.phase51_execution_planner.task_dispatcher import (
    dispatch_ready_tasks
)

from agents.phase51_execution_planner.task_executor import (
    execute_next
)

ROOT = Path(__file__).resolve().parents[2]

STATE = ROOT / "ceo_memory/phase51/execution_loop_state.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def run_loop(max_cycles=25):
    history = []

    for cycle in range(1, max_cycles + 1):
        dispatch_result = dispatch_ready_tasks()
        execute_result = execute_next()

        history.append({
            "cycle": cycle,
            "dispatch": dispatch_result,
            "execute": execute_result
        })

        status = execute_result.get("status")

        if status == "phase51_no_queued_tasks":
            break

        if status == "phase51_execution_blocked":
            break

        if not execute_result.get("success", False):
            break

    state = {
        "last_run_at": now(),
        "cycles_run": len(history),
        "last_cycle": history[-1] if history else None
    }

    save_json(STATE, state)

    return {
        "success": True,
        "status": "phase51_execution_loop_complete",
        "state": state,
        "history": history
    }


if __name__ == "__main__":
    print(json.dumps(run_loop(), indent=2))
