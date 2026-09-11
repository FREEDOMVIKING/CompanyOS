#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"
STATE = MEM / "api_usage_state.json"

def today() -> str:
    return datetime.now(timezone.utc).date().isoformat()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load() -> dict[str, Any]:
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        data = {}

    if data.get("date") != today():
        data = {
            "date": today(),
            "requests": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "updated_at": now()
        }
    return data

def save(data: dict[str, Any]) -> None:
    data["updated_at"] = now()
    STATE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def record(requests: int = 1, input_tokens: int = 0, output_tokens: int = 0) -> dict[str, Any]:
    data = load()
    data["requests"] += int(requests)
    data["input_tokens"] += int(input_tokens)
    data["output_tokens"] += int(output_tokens)
    data["total_tokens"] = data["input_tokens"] + data["output_tokens"]
    save(data)
    return data

def status() -> dict[str, Any]:
    return load()

action = sys.argv[1] if len(sys.argv) > 1 else "status"

if action == "record":
    requests = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    input_tokens = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    output_tokens = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    result = record(requests, input_tokens, output_tokens)
else:
    result = status()

print(json.dumps({
    "success": True,
    "status": "api_usage_tracker",
    "usage": result
}, indent=2))
