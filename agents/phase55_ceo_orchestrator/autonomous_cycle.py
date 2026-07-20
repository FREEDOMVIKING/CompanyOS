#!/usr/bin/env python3

import json
from datetime import datetime, timezone

from agents.phase54_collaboration.collaboration_orchestrator import (
    run_collaboration
)

from agents.phase55_ceo_orchestrator.ceo_orchestrator import (
    finalize_ceo_cycle
)


def now():
    return datetime.now(timezone.utc).isoformat()


def run_autonomous_ceo_cycle(
    objective,
    proposed_next_action="Continue internal validation and development",
    action_class="reversible_internal",
):
    cycle_id = (
        "autonomous-ceo-"
        + str(int(datetime.now(timezone.utc).timestamp() * 1000000))
    )

    collaboration = run_collaboration(
        objective=objective,
        workspace_id=cycle_id,
    )

    if not collaboration.get("success", False):
        return {
            "success": False,
            "status": "phase55_collaboration_failed",
            "cycle_id": cycle_id,
            "collaboration": collaboration,
            "completed_at": now(),
        }

    pipeline_results = {
        "phase54_status": collaboration.get("status"),
        "workspace_id": collaboration.get("workspace_id"),
        "roles_completed": collaboration.get("roles_completed", []),
        "workspace_results": collaboration.get("workspace_results", 0),
        "artifact_count": collaboration.get("artifact_count", 0),
    }

    ceo_decision = finalize_ceo_cycle(
        objective=objective,
        pipeline_results=pipeline_results,
        proposed_next_action=proposed_next_action,
        action_class=action_class,
    )

    return {
        "success": (
            collaboration.get("success") is True
            and ceo_decision.get("success") is True
        ),
        "status": "phase55_autonomous_ceo_cycle_complete",
        "cycle_id": cycle_id,
        "objective": objective,
        "collaboration": collaboration,
        "ceo_decision": ceo_decision,
        "completed_at": now(),
    }


if __name__ == "__main__":
    result = run_autonomous_ceo_cycle(
        objective=(
            "Research and develop a viable AI-powered digital business "
            "opportunity and determine the safest next execution step."
        )
    )

    print(json.dumps(result, indent=2))
