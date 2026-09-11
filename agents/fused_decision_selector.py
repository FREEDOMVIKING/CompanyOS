#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "fused_selector_config.json"
FUSED = MEM / "confidence_priority_report.json"
ELIGIBILITY = MEM / "execution_eligibility_report.json"
STATE = MEM / "fused_selector_state.json"
REPORT = MEM / "fused_selector_report.json"
HEALTH = MEM / "fused_selector_health.json"

CATEGORY_MAP = {
    "refresh-priorities": "internal_reversible",
    "refresh-decisions": "internal_reversible",
    "refresh-forecast": "internal_read_only",
    "refresh-brief": "internal_read_only",
    "refresh-goals": "internal_reversible",
    "run-learning": "internal_reversible",
    "run-health": "internal_read_only",
    "run-readiness": "internal_read_only",
    "run-outcomes": "internal_read_only",
    "github-read": "external_read_only"
}

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def load(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

def select() -> dict[str, Any]:
    cfg = load(CFG, {})
    fused = load(FUSED, {}).get("fused_priorities", [])
    eligibility_data = load(ELIGIBILITY, {})

    system_ready = eligibility_data.get("system_ready") is True
    matrix = eligibility_data.get("eligibility", {})

    minimum = float(cfg.get("minimum_fused_priority", 50))
    maximum = int(cfg.get("maximum_selected_actions", 5))

    selected = []
    rejected = []

    for item in fused:
        action = item.get("action")
        score = float(item.get("fused_priority", 0))
        category = CATEGORY_MAP.get(action, "internal_read_only")

        if score < minimum:
            rejected.append({
                "action": action,
                "fused_priority": score,
                "category": category,
                "reason": "below_minimum_fused_priority"
            })
            continue

        if cfg.get("require_execution_eligibility", True):
            if not system_ready:
                rejected.append({
                    "action": action,
                    "fused_priority": score,
                    "category": category,
                    "reason": "system_not_ready"
                })
                continue

            if not bool(matrix.get(category, False)):
                rejected.append({
                    "action": action,
                    "fused_priority": score,
                    "category": category,
                    "reason": "category_not_eligible"
                })
                continue

        selected.append({
            "action": action,
            "category": category,
            "fused_priority": round(score, 2),
            "confidence": item.get("confidence"),
            "learned_score": item.get("learned_score"),
            "adaptive_priority": item.get("adaptive_priority"),
            "reason": item.get("reason")
        })

        if len(selected) >= maximum:
            break

    report = {
        "generated_at": now(),
        "system_ready": system_ready,
        "selected_actions": selected,
        "rejected_actions": rejected,
        "selected_count": len(selected),
        "rejected_count": len(rejected),
        "automatic_external_write": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_selected_at": now(),
        "system_ready": system_ready,
        "selected_count": len(selected),
        "rejected_count": len(rejected),
        "top_selected_action": selected[0]["action"] if selected else None
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "selected_count": len(selected),
        "system_ready": system_ready
    })

    return {
        "success": True,
        "status": "fused_decision_selection_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "fused_decision_selector_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "select":
        result = select()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["select", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
