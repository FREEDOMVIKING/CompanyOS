#!/usr/bin/env python3

import importlib.util
import json
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
COMPANYOS_DIR = ROOT_DIR / "companyos"
PLUGIN_ROOT = COMPANYOS_DIR / "plugins"
INSTALLED_DIR = PLUGIN_ROOT / "installed"

REGISTRY_FILE = PLUGIN_ROOT / "registry.json"
POLICY_FILE = PLUGIN_ROOT / "policy.json"
USAGE_FILE = ROOT_DIR / "ceo_memory" / "plugin_usage.json"
EVENTS_FILE = ROOT_DIR / "ceo_memory" / "plugin_events.json"

PLUGIN_ID_PATTERN = re.compile(r"^[a-z0-9_-]+$")


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


def validate_plugin_id(plugin_id: str) -> None:
    if not PLUGIN_ID_PATTERN.fullmatch(plugin_id):
        raise ValueError(
            "Plugin IDs may contain lowercase letters, "
            "numbers, underscores, and hyphens only."
        )


def plugin_directory(plugin_id: str) -> Path:
    validate_plugin_id(plugin_id)

    path = (INSTALLED_DIR / plugin_id).resolve()
    root = INSTALLED_DIR.resolve()

    if path.parent != root:
        raise ValueError("Invalid plugin directory")

    return path


def read_manifest(plugin_id: str) -> dict[str, Any]:
    directory = plugin_directory(plugin_id)
    manifest_file = directory / "manifest.json"

    if not manifest_file.exists():
        raise FileNotFoundError(
            f"Plugin manifest missing: {plugin_id}"
        )

    manifest = load_json(manifest_file, None)

    if not isinstance(manifest, dict):
        raise ValueError(
            f"Invalid plugin manifest: {plugin_id}"
        )

    required = {
        "id",
        "name",
        "version",
        "description",
        "capabilities",
        "entrypoint",
    }

    missing = sorted(required - set(manifest))

    if missing:
        raise ValueError(
            "Manifest missing fields: " + ", ".join(missing)
        )

    if manifest["id"] != plugin_id:
        raise ValueError(
            "Manifest plugin ID does not match directory name"
        )

    if not isinstance(manifest["capabilities"], list):
        raise ValueError("Plugin capabilities must be a list")

    entrypoint = str(manifest["entrypoint"])

    if "/" in entrypoint or "\\" in entrypoint:
        raise ValueError("Plugin entrypoint must be a filename")

    return manifest


def load_plugin_module(
    plugin_id: str,
    manifest: dict[str, Any],
):
    directory = plugin_directory(plugin_id)
    entrypoint = directory / str(manifest["entrypoint"])

    if not entrypoint.exists():
        raise FileNotFoundError(
            f"Plugin entrypoint missing: {entrypoint.name}"
        )

    module_name = f"companyos_plugin_{plugin_id}"

    spec = importlib.util.spec_from_file_location(
        module_name,
        entrypoint,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Unable to load plugin: {plugin_id}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not callable(getattr(module, "run", None)):
        raise AttributeError(
            f"Plugin {plugin_id} does not define run(task)"
        )

    if not callable(getattr(module, "health_check", None)):
        raise AttributeError(
            f"Plugin {plugin_id} does not define health_check()"
        )

    return module


def load_registry() -> dict[str, Any]:
    registry = load_json(
        REGISTRY_FILE,
        {
            "registry_version": 1,
            "plugins": {},
            "updated_at": None,
        },
    )

    if not isinstance(registry, dict):
        registry = {
            "registry_version": 1,
            "plugins": {},
            "updated_at": None,
        }

    if not isinstance(registry.get("plugins"), dict):
        registry["plugins"] = {}

    return registry


def save_registry(registry: dict[str, Any]) -> None:
    registry["updated_at"] = now()
    save_json(REGISTRY_FILE, registry)


def record_event(
    plugin_id: str,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> None:
    events = load_json(EVENTS_FILE, [])

    if not isinstance(events, list):
        events = []

    events.append({
        "plugin_id": plugin_id,
        "event_type": event_type,
        "details": details or {},
        "created_at": now(),
    })

    save_json(EVENTS_FILE, events[-2000:])


def update_usage(
    plugin_id: str,
    success: bool,
) -> None:
    usage = load_json(USAGE_FILE, {})

    if not isinstance(usage, dict):
        usage = {}

    entry = usage.setdefault(
        plugin_id,
        {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run_at": None,
        },
    )

    entry["total_runs"] = int(entry["total_runs"]) + 1

    if success:
        entry["successful_runs"] = (
            int(entry["successful_runs"]) + 1
        )
    else:
        entry["failed_runs"] = (
            int(entry["failed_runs"]) + 1
        )

    entry["last_run_at"] = now()

    save_json(USAGE_FILE, usage)


def discover_plugins() -> dict[str, Any]:
    registry = load_registry()
    discovered: dict[str, Any] = {}
    errors: list[dict[str, str]] = []

    INSTALLED_DIR.mkdir(parents=True, exist_ok=True)

    for directory in sorted(INSTALLED_DIR.iterdir()):
        if not directory.is_dir():
            continue

        plugin_id = directory.name

        try:
            validate_plugin_id(plugin_id)
            manifest = read_manifest(plugin_id)

            existing = registry["plugins"].get(
                plugin_id,
                {},
            )

            discovered[plugin_id] = {
                "id": plugin_id,
                "name": manifest["name"],
                "version": manifest["version"],
                "description": manifest["description"],
                "capabilities": manifest["capabilities"],
                "permissions": manifest.get(
                    "permissions",
                    [],
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
                "installed_at": existing.get(
                    "installed_at",
                    now(),
                ),
                "updated_at": now(),
            }

        except Exception as error:
            errors.append({
                "plugin_id": plugin_id,
                "error": str(error),
            })

    registry["plugins"] = discovered
    save_registry(registry)

    return {
        "success": not errors,
        "status": "plugin_discovery_complete",
        "plugins_found": len(discovered),
        "errors": errors,
        "plugins": discovered,
    }


def list_plugins() -> dict[str, Any]:
    registry = load_registry()
    usage = load_json(USAGE_FILE, {})

    plugins = []

    for plugin_id, entry in registry["plugins"].items():
        item = dict(entry)
        item["usage"] = usage.get(
            plugin_id,
            {
                "total_runs": 0,
                "successful_runs": 0,
                "failed_runs": 0,
                "last_run_at": None,
            },
        )
        plugins.append(item)

    plugins.sort(key=lambda item: item["id"])

    return {
        "success": True,
        "status": "plugins_listed",
        "count": len(plugins),
        "plugins": plugins,
    }


def set_enabled(
    plugin_id: str,
    enabled: bool,
) -> dict[str, Any]:
    registry = load_registry()

    if plugin_id not in registry["plugins"]:
        raise KeyError(f"Unknown plugin: {plugin_id}")

    registry["plugins"][plugin_id]["enabled"] = enabled
    registry["plugins"][plugin_id]["updated_at"] = now()

    save_registry(registry)

    record_event(
        plugin_id,
        "enabled" if enabled else "disabled",
    )

    return {
        "success": True,
        "status": (
            "plugin_enabled"
            if enabled
            else "plugin_disabled"
        ),
        "plugin_id": plugin_id,
        "enabled": enabled,
    }


def health_check(plugin_id: str) -> dict[str, Any]:
    registry = load_registry()

    if plugin_id not in registry["plugins"]:
        raise KeyError(f"Unknown plugin: {plugin_id}")

    manifest = read_manifest(plugin_id)
    module = load_plugin_module(plugin_id, manifest)

    try:
        result = module.health_check()

        if not isinstance(result, dict):
            result = {
                "success": bool(result),
                "message": str(result),
            }

        healthy = result.get("success") is True

        registry["plugins"][plugin_id]["health"] = (
            "healthy" if healthy else "unhealthy"
        )
        registry["plugins"][plugin_id][
            "last_health_check_at"
        ] = now()

        save_registry(registry)

        record_event(
            plugin_id,
            "health_check",
            result,
        )

        return {
            "success": healthy,
            "plugin_id": plugin_id,
            "health": (
                "healthy" if healthy else "unhealthy"
            ),
            "result": result,
        }

    except Exception as error:
        registry["plugins"][plugin_id]["health"] = "error"
        registry["plugins"][plugin_id][
            "last_health_check_at"
        ] = now()
        registry["plugins"][plugin_id][
            "last_error"
        ] = str(error)

        save_registry(registry)

        record_event(
            plugin_id,
            "health_error",
            {"error": str(error)},
        )

        return {
            "success": False,
            "plugin_id": plugin_id,
            "health": "error",
            "error": str(error),
        }


def run_plugin(
    plugin_id: str,
    task: dict[str, Any],
) -> dict[str, Any]:
    registry = load_registry()

    plugin = registry["plugins"].get(plugin_id)

    if plugin is None:
        raise KeyError(f"Unknown plugin: {plugin_id}")

    if not plugin.get("enabled", False):
        return {
            "success": False,
            "error": f"Plugin is disabled: {plugin_id}",
        }

    manifest = read_manifest(plugin_id)
    module = load_plugin_module(plugin_id, manifest)

    try:
        result = module.run(task)

        if not isinstance(result, dict):
            result = {
                "success": True,
                "result": result,
            }

        success = result.get("success") is True
        update_usage(plugin_id, success)

        record_event(
            plugin_id,
            "run",
            {
                "success": success,
                "action": task.get("action"),
            },
        )

        return result

    except Exception as error:
        update_usage(plugin_id, False)

        record_event(
            plugin_id,
            "run_error",
            {
                "error": str(error),
                "traceback": traceback.format_exc()[-2000:],
            },
        )

        return {
            "success": False,
            "plugin_id": plugin_id,
            "error": str(error),
        }


def health_check_all() -> dict[str, Any]:
    registry = load_registry()
    results = []

    for plugin_id in registry["plugins"]:
        results.append(health_check(plugin_id))

    return {
        "success": all(
            result.get("success") is True
            for result in results
        ),
        "status": "plugin_health_scan_complete",
        "results": results,
    }
