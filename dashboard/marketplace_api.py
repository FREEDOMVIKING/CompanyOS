#!/usr/bin/env python3

import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from companyos.marketplace.manager import (  # noqa: E402
    install_plugin,
    list_marketplace,
    uninstall_plugin,
)
from companyos.plugins.runtime import discover_plugins  # noqa: E402


def marketplace_snapshot() -> dict[str, Any]:
    return list_marketplace()


def marketplace_action(
    plugin_id: str,
    action: str,
) -> dict[str, Any]:
    if action == "install":
        result = install_plugin(plugin_id)

        if result.get("success"):
            discover_plugins()

        return result

    if action == "uninstall":
        result = uninstall_plugin(plugin_id)

        if result.get("success"):
            discover_plugins()

        return result

    return {
        "success": False,
        "error": "Unsupported marketplace action",
    }
