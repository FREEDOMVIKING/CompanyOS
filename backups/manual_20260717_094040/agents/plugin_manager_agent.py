#!/usr/bin/env python3

import json
from typing import Any

from companyos.plugins.runtime import (
    discover_plugins,
    health_check,
    health_check_all,
    list_plugins,
    run_plugin,
    set_enabled,
)


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    if action == "discover_plugins":
        return discover_plugins()

    if action == "list_plugins":
        return list_plugins()

    if action == "plugin_health_check":
        plugin_id = str(
            payload.get("plugin_id", "")
        ).strip()

        if not plugin_id:
            return {
                "success": False,
                "error": "plugin_id is required",
            }

        return health_check(plugin_id)

    if action == "plugin_health_check_all":
        return health_check_all()

    if action == "enable_plugin":
        plugin_id = str(
            payload.get("plugin_id", "")
        ).strip()

        return set_enabled(plugin_id, True)

    if action == "disable_plugin":
        plugin_id = str(
            payload.get("plugin_id", "")
        ).strip()

        return set_enabled(plugin_id, False)

    if action == "run_plugin":
        plugin_id = str(
            payload.get("plugin_id", "")
        ).strip()

        plugin_task = payload.get("plugin_task", {})

        if not isinstance(plugin_task, dict):
            return {
                "success": False,
                "error": "plugin_task must be an object",
            }

        return run_plugin(plugin_id, plugin_task)

    return {
        "success": False,
        "error": f"Unsupported plugin action: {action}",
    }


if __name__ == "__main__":
    print(json.dumps(discover_plugins(), indent=2))
    print(json.dumps(list_plugins(), indent=2))
