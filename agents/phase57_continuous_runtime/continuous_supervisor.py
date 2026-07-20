#!/usr/bin/env python3

import json
import time
from datetime import datetime, timezone

from agents.phase57_continuous_runtime.runtime_controller import (
    run_runtime_cycle,
    load_state,
    save_state,
)


def now():
    return datetime.now(timezone.utc).isoformat()


def request_stop():
    state = load_state()
    state["stop_requested"] = True
    state["status"] = "stop_requested"
    save_state(state)

    return {
        "success": True,
        "status": "phase57_stop_requested",
        "requested_at": now(),
    }


def clear_stop():
    state = load_state()
    state["stop_requested"] = False
    state["status"] = "ready"
    save_state(state)

    return {
        "success": True,
        "status": "phase57_stop_cleared",
        "cleared_at": now(),
    }


def run_continuous(
    objective,
    interval_seconds=60,
    max_cycles=None,
    max_consecutive_failures=3,
):
    completed = 0

    while True:
        state = load_state()

        if state.get("stop_requested"):
            return {
                "success": True,
                "status": "phase57_continuous_runtime_stopped",
                "reason": "stop_requested",
                "cycles_this_run": completed,
                "runtime_state": state,
            }

        if (
            max_cycles is not None
            and completed >= max_cycles
        ):
            return {
                "success": True,
                "status": "phase57_max_cycles_reached",
                "cycles_this_run": completed,
                "runtime_state": state,
            }

        result = run_runtime_cycle(
            objective=objective,
            proposed_next_action=(
                "Continue internal validation and development"
            ),
            action_class="reversible_internal",
        )

        completed += 1
        state = load_state()

        if (
            state.get("consecutive_failures", 0)
            >= max_consecutive_failures
        ):
            state["status"] = "halted_failure_threshold"
            state["stop_requested"] = True
            save_state(state)

            return {
                "success": False,
                "status": "phase57_failure_threshold_reached",
                "cycles_this_run": completed,
                "last_result": result,
                "runtime_state": state,
            }

        if max_cycles is None or completed < max_cycles:
            time.sleep(max(1, interval_seconds))


if __name__ == "__main__":
    print(json.dumps({
        "success": True,
        "status": "phase57_continuous_supervisor_ready",
        "runtime_state": load_state(),
    }, indent=2))
