#!/usr/bin/env python3

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
MARKET_DIR = ROOT_DIR / "companyos" / "marketplace"
PACKAGES_DIR = MARKET_DIR / "packages"
PLUGIN_DIR = ROOT_DIR / "companyos" / "plugins"
INSTALLED_DIR = PLUGIN_DIR / "installed"

CATALOG_FILE = MARKET_DIR / "catalog.json"
EVENT_FILE = ROOT_DIR / "ceo_memory" / "marketplace_events.json"

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


def record_event(
    plugin_id: str,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> None:
    events = load_json(EVENT_FILE, [])

    if not isinstance(events, list):
        events = []

    events.append({
        "plugin_id": plugin_id,
        "event_type": event_type,
        "details": details or {},
        "created_at": now(),
    })

    save_json(EVENT_FILE, events[-2000:])


def validate_plugin_id(plugin_id: str) -> None:
    if not PLUGIN_ID_PATTERN.fullmatch(plugin_id):
        raise ValueError("Invalid plugin ID")


def catalog() -> list[dict[str, Any]]:
    data = load_json(CATALOG_FILE, {})
    plugins = data.get("plugins", [])

    if not isinstance(plugins, list):
        return []

    return [
        item
        for item in plugins
        if isinstance(item, dict)
    ]


def find_catalog_plugin(plugin_id: str) -> dict[str, Any]:
    validate_plugin_id(plugin_id)

    plugin = next(
        (
            item
            for item in catalog()
            if item.get("id") == plugin_id
        ),
        None,
    )

    if plugin is None:
        raise KeyError(f"Marketplace plugin not found: {plugin_id}")

    return plugin


def list_marketplace() -> dict[str, Any]:
    installed_ids = {
        directory.name
        for directory in INSTALLED_DIR.iterdir()
        if directory.is_dir()
    } if INSTALLED_DIR.exists() else set()

    plugins = []

    for item in catalog():
        entry = dict(item)
        entry["installed"] = item.get("id") in installed_ids
        plugins.append(entry)

    return {
        "success": True,
        "status": "marketplace_listed",
        "count": len(plugins),
        "plugins": plugins,
    }


def install_plugin(plugin_id: str) -> dict[str, Any]:
    plugin = find_catalog_plugin(plugin_id)
    package_name = str(plugin.get("package", "")).strip()

    validate_plugin_id(package_name)

    source = (PACKAGES_DIR / package_name).resolve()
    destination = (INSTALLED_DIR / plugin_id).resolve()

    if source.parent != PACKAGES_DIR.resolve():
        raise ValueError("Invalid marketplace package path")

    if destination.parent != INSTALLED_DIR.resolve():
        raise ValueError("Invalid plugin destination path")

    if not source.exists():
        raise FileNotFoundError(
            f"Marketplace package is missing: {package_name}"
        )

    if destination.exists():
        return {
            "success": False,
            "error": f"Plugin is already installed: {plugin_id}",
        }

    manifest = load_json(source / "manifest.json", None)

    if not isinstance(manifest, dict):
        raise ValueError("Package manifest is invalid")

    if manifest.get("id") != plugin_id:
        raise ValueError("Package manifest ID mismatch")

    shutil.copytree(source, destination)

    record_event(
        plugin_id,
        "installed",
        {"version": plugin.get("version")},
    )

    return {
        "success": True,
        "status": "marketplace_plugin_installed",
        "plugin_id": plugin_id,
    }


def uninstall_plugin(plugin_id: str) -> dict[str, Any]:
    find_catalog_plugin(plugin_id)

    destination = (INSTALLED_DIR / plugin_id).resolve()

    if destination.parent != INSTALLED_DIR.resolve():
        raise ValueError("Invalid plugin destination path")

    if not destination.exists():
        return {
            "success": False,
            "error": f"Plugin is not installed: {plugin_id}",
        }

    shutil.rmtree(destination)

    record_event(plugin_id, "uninstalled")

    return {
        "success": True,
        "status": "marketplace_plugin_uninstalled",
        "plugin_id": plugin_id,
    }
