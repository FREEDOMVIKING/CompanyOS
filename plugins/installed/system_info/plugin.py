#!/usr/bin/env python3

import shutil
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[3]


def health_check() -> dict[str, Any]:
    return {
        "success": ROOT_DIR.exists(),
        "status": "healthy",
        "root_directory": str(ROOT_DIR),
    }


def run(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action == "get_system_info":
        usage = shutil.disk_usage(ROOT_DIR)

        return {
            "success": True,
            "status": "system_info_collected",
            "python_version": sys.version,
            "project_root": str(ROOT_DIR),
            "disk": {
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
            },
        }

    return {
        "success": False,
        "error": f"Unsupported system action: {action}",
    }
