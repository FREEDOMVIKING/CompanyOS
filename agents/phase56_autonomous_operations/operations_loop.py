#!/usr/bin/env python3

import json
from datetime import datetime, timezone

from agents.phase55_ceo_orchestrator.autonomous_cycle import (
    run_autonomous_ceo_cycle
)

from agents.phase56_autonomous_operations.operations_state import (
    begin_cycle,
    complete_cycle,
    load_state
)


def now():
    return datetime.now(timezone.utc).isoformat()


def make_cycle_id():
    return (
        "phase56-cycle-"
        + str(int(datetime.now(timezone.utc).timestamp() * 1000000))
    )


def run_operations_cycle(
    objective,
    proposed_next_action="Continue internal validation and development",
    action_class="reversible_internal",
):
    cycle_id = make_cycle_id()

    begin_cycle(
        cycle_id=cycle_id,
        objective=objective
    )

    try:
        result = run_autonomous_ceo_cycle(
            objective=objective,
            proposed_next_action=proposed_next_action,
            action_class=action_class
        )

        complete_cycle(
            cycle_id=cycle_id,
            result=result
        )

        return {
            "success": result.get("success", False),
            "status": "phase56_operations_cycle_complete",
            "cycle_id": cycle_id,
            "objective": objective,
            "ceo_cycle": result,
            "operations_state": load_state(),
            "completed_at": now()
        }

    except Exception as exc:
        failure = {
            "success": False,
            "status": "phase56_operations_cycle_failed",
            "error": str(exc)
        }

        complete_cycle(
            cycle_id=cycle_id,
            result=failure
        )

        return {
            "success": False,
            "status": "phase56_operations_cycle_failed",
            "cycle_id": cycle_id,
            "objective": objective,
            "error": str(exc),
            "operations_state": load_state(),
            "completed_at": now()
        }


if __name__ == "__main__":
    result = run_operations_cycle(
        objective=(
            "Evaluate and advance a viable AI-powered digital business "
            "through the safest permitted autonomous next steps."
        )
    )

    print(json.dumps(result, indent=2))
