#!/usr/bin/env python3

import importlib.util
import json
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONNECTOR_ROOT = ROOT_DIR / "companyos" / "connectors"
INSTALLED_DIR = CONNECTOR_ROOT / "installed"

REGISTRY_FILE = CONNECTOR_ROOT / "registry.json"
POLICY_FILE = CONNECTOR_ROOT / "policy.json"

EVENTS_FILE = ROOT_DIR / "ceo_memory" / "connector_events.json"
USAGE_FILE = ROOT_DIR / "ceo_memory" / "connector_usage.json"

ID_PATTERN = re.compile(r"^[a-z0-9_-]+$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def validate_id(connector_id: str) -> None:
    if not ID_PATTERN.fullmatch(connector_id):
        raise ValueError("Invalid connector ID")


def connector_directory(connector_id: str) -> Path:
    validate_id(connector_id)

    path = (INSTALLED_DIR / connector_id).resolve()
    root = INSTALLED_DIR.resolve()

    if path.parent != root:
        raise ValueError("Invalid connector path")

    return path


def load_registry() -> dict[str, Any]:
    registry = load_json(
        REGISTRY_FILE,
        {
            "registry_version": 1,
            "connectors": {},
            "updated_at": None,
        },
    )

    if not isinstance(registry, dict):
        registry = {
            "registry_version": 1,
            "connectors": {},
            "updated_at": None,
        }

    if not isinstance(registry.get("connectors"), dict):
        registry["connectors"] = {}

    return registry


def save_registry(registry: dict[str, Any]) -> None:
    registry["updated_at"] = now()
    save_json(REGISTRY_FILE, registry)


def record_event(
    connector_id: str,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> None:
    events = load_json(EVENTS_FILE, [])

    if not isinstance(events, list):
        events = []

    events.append({
        "connector_id": connector_id,
        "event_type": event_type,
        "details": details or {},
        "created_at": now(),
    })

    save_json(EVENTS_FILE, events[-2000:])


def update_usage(
    connector_id: str,
    success: bool,
) -> None:
    usage = load_json(USAGE_FILE, {})

    if not isinstance(usage, dict):
        usage = {}

    item = usage.setdefault(
        connector_id,
        {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run_at": None,
        },
    )

    item["total_runs"] = int(item["total_runs"]) + 1

    if success:
        item["successful_runs"] = (
            int(item["successful_runs"]) + 1
        )
    else:
        item["failed_runs"] = (
            int(item["failed_runs"]) + 1
        )

    item["last_run_at"] = now()

    save_json(USAGE_FILE, usage)


def read_manifest(
    connector_id: str,
) -> dict[str, Any]:
    directory = connector_directory(connector_id)
    path = directory / "manifest.json"
    manifest = load_json(path, None)

    if not isinstance(manifest, dict):
        raise ValueError(
            f"Invalid connector manifest: {connector_id}"
        )

    required = {
        "id",
        "name",
        "version",
        "marketplace",
        "entrypoint",
        "capabilities",
    }

    missing = required - set(manifest)

    if missing:
        raise ValueError(
            "Manifest missing fields: "
            + ", ".join(sorted(missing))
        )

    if manifest["id"] != connector_id:
        raise ValueError("Connector ID mismatch")

    entrypoint = str(manifest["entrypoint"])

    if "/" in entrypoint or "\\" in entrypoint:
        raise ValueError("Invalid connector entrypoint")

    return manifest


def load_connector(
    connector_id: str,
    manifest: dict[str, Any],
):
    path = (
        connector_directory(connector_id)
        / str(manifest["entrypoint"])
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Connector entrypoint missing: {path}"
        )

    spec = importlib.util.spec_from_file_location(
        f"companyos_connector_{connector_id}",
        path,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Unable to load connector: {connector_id}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not callable(getattr(module, "health_check", None)):
        raise AttributeError(
            "Connector must define health_check()"
        )

    if not callable(getattr(module, "publish", None)):
        raise AttributeError(
            "Connector must define publish(listing, product)"
        )

    return module


def discover_connectors() -> dict[str, Any]:
    registry = load_registry()
    discovered: dict[str, Any] = {}
    errors = []

    INSTALLED_DIR.mkdir(parents=True, exist_ok=True)

    for directory in sorted(INSTALLED_DIR.iterdir()):
        if not directory.is_dir():
            continue

        connector_id = directory.name

        try:
            manifest = read_manifest(connector_id)
            existing = registry["connectors"].get(
                connector_id,
                {},
            )

            discovered[connector_id] = {
                "id": connector_id,
                "name": manifest["name"],
                "version": manifest["version"],
                "marketplace": manifest["marketplace"],
                "description": manifest.get(
                    "description",
                    "",
                ),
                "capabilities": manifest["capabilities"],
                "external": bool(
                    manifest.get("external", True)
                ),
                "enabled": bool(
                    existing.get(
                        "enabled",
                        manifest.get(
                            "enabled_by_default",
                            False,
                        ),
                    )
                ),
                "health": existing.get(
                    "health",
                    "not_checked",
                ),
                "installed_at": existing.get(
                    "installed_at",
                    now(),
                ),
                "updated_at": now(),
            }

        except Exception as error:
            errors.append({
                "connector_id": connector_id,
                "error": str(error),
            })

    registry["connectors"] = discovered
    save_registry(registry)

    return {
        "success": not errors,
        "status": "connector_discovery_complete",
        "count": len(discovered),
        "connectors": discovered,
        "errors": errors,
    }


def list_connectors() -> dict[str, Any]:
    registry = load_registry()
    usage = load_json(USAGE_FILE, {})

    connectors = []

    for connector_id, item in registry["connectors"].items():
        entry = dict(item)
        entry["usage"] = usage.get(
            connector_id,
            {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "last_run_at": None,
            },
        )
        connectors.append(entry)

    connectors.sort(key=lambda item: item["id"])

    return {
        "success": True,
        "status": "connectors_listed",
        "count": len(connectors),
        "connectors": connectors,
    }


def set_enabled(
    connector_id: str,
    enabled: bool,
) -> dict[str, Any]:
    registry = load_registry()

    if connector_id not in registry["connectors"]:
        raise KeyError(
            f"Unknown connector: {connector_id}"
        )

    registry["connectors"][connector_id]["enabled"] = enabled
    registry["connectors"][connector_id]["updated_at"] = now()

    save_registry(registry)

    record_event(
        connector_id,
        "enabled" if enabled else "disabled",
    )

    return {
        "success": True,
        "status": (
            "connector_enabled"
            if enabled
            else "connector_disabled"
        ),
        "connector_id": connector_id,
        "enabled": enabled,
    }


def health_check(
    connector_id: str,
) -> dict[str, Any]:
    registry = load_registry()

    if connector_id not in registry["connectors"]:
        raise KeyError(
            f"Unknown connector: {connector_id}"
        )

    manifest = read_manifest(connector_id)
    module = load_connector(connector_id, manifest)

    try:
        result = module.health_check()

        if not isinstance(result, dict):
            result = {
                "success": bool(result),
                "message": str(result),
            }

        healthy = result.get("success") is True

        registry["connectors"][connector_id]["health"] = (
            "healthy" if healthy else "unhealthy"
        )
        registry["connectors"][connector_id][
            "last_health_check_at"
        ] = now()

        save_registry(registry)

        record_event(
            connector_id,
            "health_check",
            result,
        )

        return {
            "success": healthy,
            "connector_id": connector_id,
            "health": (
                "healthy" if healthy else "unhealthy"
            ),
            "result": result,
        }

    except Exception as error:
        registry["connectors"][connector_id][
            "health"
        ] = "error"
        registry["connectors"][connector_id][
            "last_error"
        ] = str(error)

        save_registry(registry)

        return {
            "success": False,
            "connector_id": connector_id,
            "health": "error",
            "error": str(error),
        }


def publish_listing(
    connector_id: str,
    listing: dict[str, Any],
    product: dict[str, Any],
    owner_approved: bool,
) -> dict[str, Any]:
    registry = load_registry()
    connector = registry["connectors"].get(connector_id)

    if connector is None:
        return {
            "success": False,
            "error": f"Unknown connector: {connector_id}",
        }

    if not connector.get("enabled", False):
        return {
            "success": False,
            "error": f"Connector disabled: {connector_id}",
        }

    if (
        connector.get("external", True)
        and not owner_approved
    ):
        return {
            "success": False,
            "status": "owner_approval_required",
            "error": (
                "External publication requires explicit "
                "owner approval"
            ),
        }

    manifest = read_manifest(connector_id)
    module = load_connector(connector_id, manifest)

    try:
        result = module.publish(
            listing=listing,
            product=product,
        )

        if not isinstance(result, dict):
            result = {
                "success": True,
                "result": result,
            }

        success = result.get("success") is True
        update_usage(connector_id, success)

        record_event(
            connector_id,
            "publish",
            {
                "success": success,
                "listing_id": listing.get("id"),
                "product_id": product.get("id"),
            },
        )

        return result

    except Exception as error:
        update_usage(connector_id, False)

        record_event(
            connector_id,
            "publish_error",
            {
                "listing_id": listing.get("id"),
                "error": str(error),
                "traceback": traceback.format_exc()[-2000:],
            },
        )

        return {
            "success": False,
            "connector_id": connector_id,
            "error": str(error),
        }
