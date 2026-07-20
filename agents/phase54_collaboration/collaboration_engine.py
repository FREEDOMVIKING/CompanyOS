#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "ceo_memory/phase54"
WORKSPACES = MEMORY / "workspaces.json"
STATE = MEMORY / "collaboration_state.json"


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


def get_workspace(workspace_id):
    data = load_json(WORKSPACES, {"workspaces": {}})

    return data.get("workspaces", {}).get(
        workspace_id,
        {
            "workspace_id": workspace_id,
            "created_at": now(),
            "updated_at": now(),
            "results": [],
            "artifacts": [],
            "roles_completed": []
        }
    )


def add_result(workspace_id, role, result):
    data = load_json(WORKSPACES, {"workspaces": {}})

    workspace = data.setdefault(
        "workspaces", {}
    ).setdefault(
        workspace_id,
        {
            "workspace_id": workspace_id,
            "created_at": now(),
            "updated_at": now(),
            "results": [],
            "artifacts": [],
            "roles_completed": []
        }
    )

    entry = {
        "role": role,
        "recorded_at": now(),
        "result": result
    }

    workspace["results"].append(entry)

    artifact = result.get("phase53_artifact")
    if artifact:
        workspace["artifacts"].append(artifact)

    if role not in workspace["roles_completed"]:
        workspace["roles_completed"].append(role)

    workspace["updated_at"] = now()

    save_json(WORKSPACES, data)

    state = {
        "last_run_at": now(),
        "last_workspace_id": workspace_id,
        "last_role": role,
        "total_workspace_results": len(workspace["results"])
    }

    save_json(STATE, state)

    return workspace


def build_context(workspace_id):
    workspace = get_workspace(workspace_id)

    prior_results = []

    for entry in workspace.get("results", []):
        result = entry.get("result", {})

        prior_results.append({
            "role": entry.get("role"),
            "summary": result.get("output", {}).get("summary"),
            "findings": result.get("output", {}).get("findings", []),
            "recommendations": result.get(
                "output", {}
            ).get("recommendations", []),
            "risks": result.get("output", {}).get("risks", [])
        })

    return {
        "workspace_id": workspace_id,
        "prior_results": prior_results,
        "roles_completed": workspace.get("roles_completed", []),
        "artifact_count": len(workspace.get("artifacts", []))
    }


def status():
    data = load_json(WORKSPACES, {"workspaces": {}})

    return {
        "success": True,
        "status": "phase54_collaboration_status",
        "state": load_json(
            STATE,
            {
                "last_run_at": None,
                "last_workspace_id": None,
                "last_role": None,
                "total_workspace_results": 0
            }
        ),
        "workspace_count": len(data.get("workspaces", {}))
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
