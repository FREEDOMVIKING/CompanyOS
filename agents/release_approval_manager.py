#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"
RELEASES = ROOT / "releases"

CONFIG = MEMORY / "release_approval_config.json"
REGISTRY = MEMORY / "release_registry.json"
AUDIT = MEMORY / "release_approval_audit.json"
STATE = MEMORY / "release_activation_state.json"
HEALTH = MEMORY / "release_approval_health.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT, [])
    if not isinstance(records, list):
        records = []
    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })
    save_json(AUDIT, records[-1000:])


def latest_release() -> tuple[dict[str, Any], dict[str, Any]]:
    store = load_json(REGISTRY, {})
    releases = store.get("releases", [])
    if not releases:
        raise RuntimeError("No packaged release found")
    return store, releases[-1]


def update_stats(store: dict[str, Any]) -> None:
    releases = store.get("releases", [])
    store["statistics"] = {
        "total": len(releases),
        "ready": sum(
            1 for item in releases
            if item.get("status") in {"packaged", "approved", "active"}
        ),
        "blocked": sum(
            1 for item in releases if item.get("status") == "blocked"
        ),
        "packaged": sum(
            1 for item in releases if item.get("status") == "packaged"
        ),
        "approved": sum(
            1 for item in releases if item.get("status") == "approved"
        ),
        "active": sum(
            1 for item in releases if item.get("status") == "active"
        ),
    }
    store["last_updated_at"] = now()


def approve_latest(reason: str | None = None) -> dict[str, Any]:
    store, release = latest_release()

    if release.get("status") not in {"packaged", "approved"}:
        result = {
            "success": False,
            "status": "release_approval_blocked",
            "reason": f"Release status is {release.get('status')}",
        }
        audit("approve", result)
        return result

    release["status"] = "approved"
    release["owner_approved"] = True
    release["owner_approval_reason"] = reason
    release["approved_at"] = now()
    release["updated_at"] = now()

    update_stats(store)
    save_json(REGISTRY, store)

    result = {
        "success": True,
        "status": "release_approved",
        "release_id": release.get("release_id"),
        "reason": reason,
        "automatic_local_activation": False,
        "automatic_external_deployment": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    audit("approve", result)
    return result


def activate_latest() -> dict[str, Any]:
    store, release = latest_release()

    if release.get("status") not in {"approved", "active"}:
        result = {
            "success": False,
            "status": "local_activation_blocked",
            "reason": "Release must be owner-approved first",
            "current_status": release.get("status"),
        }
        audit("activate", result)
        return result

    source = Path(str(release.get("directory", "")))

    if not source.exists():
        result = {
            "success": False,
            "status": "release_directory_missing",
            "directory": str(source),
        }
        audit("activate", result)
        return result

    active_root = RELEASES / "active"

    if active_root.exists():
        shutil.rmtree(active_root)

    shutil.copytree(source, active_root)

    release["status"] = "active"
    release["active_directory"] = str(active_root)
    release["activated_at"] = now()
    release["updated_at"] = now()

    update_stats(store)
    save_json(REGISTRY, store)

    state = {
        "active_release_id": release.get("release_id"),
        "active_directory": str(active_root),
        "activated_at": now(),
        "status": "active",
        "preview_command": f"python {active_root / 'server.py'}",
        "preview_url": "http://127.0.0.1:8765",
        "external_deployment": False,
        "external_publication": False,
    }

    save_json(STATE, state)
    save_json(
        HEALTH,
        {
            "healthy": True,
            "active_release_id": release.get("release_id"),
            "active_directory": str(active_root),
            "last_error": None,
            "updated_at": now(),
        },
    )

    result = {
        "success": True,
        "status": "release_locally_activated",
        "release_id": release.get("release_id"),
        "active_directory": str(active_root),
        "preview_command": state["preview_command"],
        "preview_url": state["preview_url"],
        "automatic_external_deployment": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    audit("activate", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    store = load_json(REGISTRY, {})
    state = load_json(STATE, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "release_approval_status",
        "enabled": config.get("enabled", False),
        "owner_approval_required": config.get("owner_approval_required", True),
        "automatic_release_approval": config.get(
            "automatic_release_approval", False
        ),
        "automatic_local_activation": config.get(
            "automatic_local_activation", False
        ),
        "automatic_external_deployment": config.get(
            "automatic_external_deployment", False
        ),
        "automatic_publication": config.get("automatic_publication", False),
        "automatic_spending": config.get("automatic_spending", False),
        "release_statistics": store.get("statistics", {}),
        "activation_state": state,
        "health": health,
    }

    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "approve-latest":
            reason = " ".join(sys.argv[2:]).strip() or None
            return print_result(approve_latest(reason))

        if action == "activate-latest":
            return print_result(activate_latest())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_release_approval_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "release_approval_error",
            "error": str(exc),
        }
        save_json(
            HEALTH,
            {
                "healthy": False,
                "last_checked_at": now(),
                "last_error": str(exc),
            },
        )
        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
