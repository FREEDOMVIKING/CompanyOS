#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"
CFG = MEM / "model_fallback_config.json"

def load() -> dict[str, Any]:
    try:
        return json.loads(CFG.read_text(encoding="utf-8"))
    except Exception:
        return {"enabled": True, "models": ["openrouter/free"]}

def models() -> list[str]:
    cfg = load()
    values = cfg.get("models", ["openrouter/free"])
    return [str(x) for x in values if x] or ["openrouter/free"]

def primary_model() -> str:
    return models()[0]

if __name__ == "__main__":
    print(json.dumps({
        "success": True,
        "status": "model_fallback_router_status",
        "models": models(),
        "primary_model": primary_model()
    }, indent=2))
