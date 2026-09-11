#!/usr/bin/env python3

import re
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from companyos.plugins.runtime import (  # noqa: E402
    discover_plugins,
    health_check,
    list_plugins,
    set_enabled,
)

PLUGIN_ID_PATTERN = re.compile(r"^[a-z0-9_-]+$")

ALLOWED_PLUGIN_ACTIONS = {
    "enable",
    "disable",
    "health",
}


def validate_plugin_id(plugin_id: str) -> None:
    if not PLUGIN_ID_PATTERN.fullmatch(plugin_id):
        raise ValueError("Invalid plugin ID")


def plugin_snapshot() -> dict[str, Any]:
    result = list_plugins()

    plugins = result.get("plugins", [])

    if not isinstance(plugins, list):
        plugins = []

    return {
        "success": True,
        "status": "plugins_loaded",
        "count": len(plugins),
        "plugins": plugins,
    }


def discover_plugin_snapshot() -> dict[str, Any]:
    discovery = discover_plugins()
    listing = list_plugins()

    return {
        "success": discovery.get("success", False),
        "status": "plugin_discovery_complete",
        "plugins_found": discovery.get("plugins_found", 0),
        "errors": discovery.get("errors", []),
        "plugins": listing.get("plugins", []),
    }


def perform_plugin_action(
    plugin_id: str,
    action: str,
) -> dict[str, Any]:
    validate_plugin_id(plugin_id)

    if action not in ALLOWED_PLUGIN_ACTIONS:
        return {
            "success": False,
            "error": "Unsupported plugin action",
        }

    if action == "enable":
        return set_enabled(plugin_id, True)

    if action == "disable":
        return set_enabled(plugin_id, False)

    if action == "health":
        return health_check(plugin_id)

    return {
        "success": False,
        "error": "Unsupported plugin action",
    }
