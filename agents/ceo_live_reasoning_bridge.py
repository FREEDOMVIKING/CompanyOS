#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

INSIGHTS = MEM / "validated_insights.json"
DECISIONS = MEM / "ceo_decision_candidates.json"
OUT = MEM / "ceo_live_reasoning_input.json"

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def build() -> dict[str, Any]:
    insights = load(INSIGHTS, {}).get("insights", [])
    decisions = load(DECISIONS, {}).get("decisions", [])

    payload = {
        "generated_at": now(),
        "validated_insights": insights[-50:],
        "decision_candidates": decisions[-50:],
        "reasoning_boundary": "internal_non_destructive_only",
        "external_authority_granted": False
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload

if __name__ == "__main__":
    print(json.dumps({
        "success": True,
        "status": "ceo_live_reasoning_bridge_complete",
        "payload": build()
    }, indent=2))
