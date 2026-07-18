#!/usr/bin/env python3

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "ceo_memory" / "knowledge_notes"
SAFE_NAME = re.compile(r"^[a-zA-Z0-9_.-]+$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_path(name: str) -> Path:
    if not SAFE_NAME.fullmatch(name):
        raise ValueError("Invalid note name")

    path = (DATA_DIR / f"{name}.json").resolve()

    if path.parent != DATA_DIR.resolve():
        raise ValueError("Invalid note path")

    return path


def health_check() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    return {
        "success": True,
        "status": "healthy",
        "note_directory": str(DATA_DIR),
    }


def run(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if action == "create_note":
        name = str(payload.get("name", "")).strip()
        content = payload.get("content")

        if not name:
            return {
                "success": False,
                "error": "Note name is required",
            }

        path = safe_path(name)

        data = {
            "name": name,
            "content": content,
            "created_at": now(),
        }

        path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

        return {
            "success": True,
            "status": "note_created",
            "name": name,
        }

    if action == "read_note":
        name = str(payload.get("name", "")).strip()
        path = safe_path(name)

        if not path.exists():
            return {
                "success": False,
                "error": "Note does not exist",
            }

        return {
            "success": True,
            "status": "note_read",
            "note": json.loads(
                path.read_text(encoding="utf-8")
            ),
        }

    if action == "list_notes":
        notes = sorted(
            path.stem
            for path in DATA_DIR.glob("*.json")
        )

        return {
            "success": True,
            "status": "notes_listed",
            "notes": notes,
        }

    if action == "search_notes":
        query = str(payload.get("query", "")).lower().strip()
        matches = []

        for path in DATA_DIR.glob("*.json"):
            text = path.read_text(
                encoding="utf-8"
            ).lower()

            if query in text:
                matches.append(path.stem)

        return {
            "success": True,
            "status": "notes_searched",
            "query": query,
            "matches": sorted(matches),
        }

    return {
        "success": False,
        "error": f"Unsupported knowledge action: {action}",
    }
