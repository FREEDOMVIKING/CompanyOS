#!/usr/bin/env python3

import json
import time
import traceback

from agents.phase57_continuous_runtime.continuous_supervisor import (
    clear_stop,
    run_continuous,
)

from agents.phase58_persistent_runtime.runtime_state import (
    load_state,
    save_state,
    mark_started,
    mark_stopped,
    heartbeat,
)


def run_worker(
    objective="Continuously evaluate and develop viable AI-powered business opportunities using safe reversible internal actions.",
    interval_seconds=60,
    cycles_per_batch=1,
):
    state = load_state()

    # Prevent accidental duplicate logical starts.
    if state.get("status") == "running" and state.get("pid"):
        return {
            "success": False,
            "status": "phase58_already_running",
            "pid": state.get("pid"),
        }

    clear_stop()
    mark_started()

    try:
        while True:
            state = load_state()

            if state.get("stop_requested"):
                break

            heartbeat()

            result = run_continuous(
                objective=objective,
                interval_seconds=interval_seconds,
                max_cycles=cycles_per_batch,
                max_consecutive_failures=3,
            )

            state = load_state()
            state["cycles_this_session"] = (
                state.get("cycles_this_session", 0)
                + result.get("cycles_this_run", 0)
            )
            state["last_result_status"] = result.get("status")
            state["last_heartbeat"] = heartbeat().get("last_heartbeat")
            save_state(state)

            if not result.get("success", False):
                state = load_state()
                state["last_error"] = result.get("status")
                save_state(state)
                break

            time.sleep(interval_seconds)

        final_state = mark_stopped()

        return {
            "success": True,
            "status": "phase58_worker_stopped",
            "state": final_state,
        }

    except KeyboardInterrupt:
        final_state = mark_stopped()

        return {
            "success": True,
            "status": "phase58_worker_interrupted",
            "state": final_state,
        }

    except Exception as exc:
        state = load_state()
        state["status"] = "crashed"
        state["last_error"] = str(exc)
        state["last_traceback"] = traceback.format_exc()
        state["pid"] = None
        save_state(state)

        return {
            "success": False,
            "status": "phase58_worker_crashed",
            "error": str(exc),
        }


if __name__ == "__main__":
    print(json.dumps({
        "success": True,
        "status": "phase58_persistent_worker_ready",
    }, indent=2))
