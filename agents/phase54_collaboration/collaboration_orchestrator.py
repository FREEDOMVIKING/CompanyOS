#!/usr/bin/env python3

from datetime import datetime, timezone

from agents.phase52_specialist_runtime.runtime import run_specialist
from agents.phase54_collaboration.collaboration_engine import (
    add_result,
    build_context,
    get_workspace,
)

SPECIALIST_CHAIN = [
    (
        "research_agent",
        "Analyze the opportunity, evidence, assumptions, market demand, competition, and risks."
    ),
    (
        "strategy_agent",
        "Turn validated research into a practical business and execution strategy."
    ),
    (
        "builder_agent",
        "Design the product, technical architecture, implementation plan, tests, and deliverables."
    ),
    (
        "growth_agent",
        "Design customer acquisition, positioning, pricing, validation, revenue, and growth strategy."
    ),
    (
        "ceo_agent",
        "Synthesize all specialist work into an executive decision package and recommended next actions."
    ),
]


def now():
    return datetime.now(timezone.utc).isoformat()


def run_collaboration(objective, workspace_id=None):
    if workspace_id is None:
        workspace_id = (
            "collab-"
            + str(int(datetime.now(timezone.utc).timestamp() * 1000000))
        )

    executions = []

    for role, mission in SPECIALIST_CHAIN:
        context = build_context(workspace_id)

        result = run_specialist(
            role=role,
            task=f"{mission} Overall objective: {objective}",
            context=context,
        )

        workspace = add_result(
            workspace_id=workspace_id,
            role=role,
            result=result,
        )

        executions.append({
            "role": role,
            "success": result.get("success", False),
            "prior_results_received": len(
                context.get("prior_results", [])
            ),
        })

        if not result.get("success", False):
            return {
                "success": False,
                "status": "phase54_collaboration_failed",
                "workspace_id": workspace_id,
                "failed_role": role,
                "executions": executions,
                "workspace": workspace,
                "completed_at": now(),
            }

    workspace = get_workspace(workspace_id)

    return {
        "success": True,
        "status": "phase54_collaboration_complete",
        "workspace_id": workspace_id,
        "objective": objective,
        "executions": executions,
        "roles_completed": workspace.get("roles_completed", []),
        "workspace_results": len(workspace.get("results", [])),
        "artifact_count": len(workspace.get("artifacts", [])),
        "completed_at": now(),
    }
