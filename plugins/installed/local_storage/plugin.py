#!/usr/bin/env python3

import json
import re
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "companyos" / "plugin_data"
SAFE_NAME = re.compile(r"^[a-zA-Z0-9_.-]+$")


def health_check() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    return {
        "success": DATA_DIR.exists(),
        "status": "healthy",
        "data_directory": str(DATA_DIR),
    }


def safe_path(filename: str) -> Path:
    if not SAFE_NAME.fullmatch(filename):
        raise ValueError("Invalid filename")

    path = (DATA_DIR / filename).resolve()
    root = DATA_DIR.resolve()

    if path.parent != root:
        raise ValueError("Invalid storage path")

    return path


def run(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if action == "write_json":
        filename = str(
            payload.get("filename", "")
        ).strip()

        data = payload.get("data")

        if not filename.endswith(".json"):
            return {
                "success": False,
                "error": "Only .json files are allowed",
            }

        path = safe_path(filename)
        temporary = path.with_suffix(".json.tmp")

        temporary.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)

        return {
            "success": True,
            "status": "json_written",
            "filename": filename,
        }

    if action == "read_json":
        filename = str(
            payload.get("filename", "")
        ).strip()

        path = safe_path(filename)

        if not path.exists():
            return {
                "success": False,
                "error": "File does not exist",
            }

        return {
            "success": True,
            "status": "json_read",
            "filename": filename,
            "data": json.loads(
                path.read_text(encoding="utf-8")
            ),
        }

    if action == "list_files":
        files = sorted(
            path.name
            for path in DATA_DIR.iterdir()
            if path.is_file()
        )

        return {
            "success": True,
            "status": "files_listed",
            "files": files,
        }

    return {
        "success": False,
        "error": f"Unsupported storage action: {action}",
    }
