#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "feedback_priority_config.json"
FUSED = MEM / "confidence_priority_report.json"
FEEDBACK = MEM / "execution_feedback_report.json"

STATE = MEM / "feedback_priority_state.json"
REPORT = MEM / "feedback_priority_report.json"
HEALTH = MEM / "feedback_priority_health.json"

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

def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))

def integrate() -> dict[str, Any]:
    cfg = load(CFG, {})
    fused = load(FUSED, {}).get("fused_priorities", [])
    feedback_rows = load(FEEDBACK, {}).get("adjustments", [])

    feedback = {
        row.get("action"): row
        for row in feedback_rows
        if row.get("action")
    }

    fw = float(cfg.get("feedback_weight", 0.25))
    pw = float(cfg.get("fused_priority_weight", 0.75))
    total_weight = fw + pw
    if total_weight <= 0:
        fw, pw, total_weight = 0.25, 0.75, 1.0

    low = float(cfg.get("minimum_priority", 1))
    high = float(cfg.get("maximum_priority", 100))

    integrated = []

    for row in fused:
        action = row.get("action")
        if not action:
            continue

        base = float(row.get("fused_priority", 50))
        fb = feedback.get(action, {})
        adjustment = float(fb.get("feedback_adjustment", 0))
        confidence = float(fb.get("confidence", 0))

        adjusted_target = clamp(base + adjustment, low, high)

        final_priority = (
            (base * pw) +
            (adjusted_target * fw)
        ) / total_weight

        final_priority = clamp(final_priority, low, high)

        integrated.append({
            "action": action,
            "base_fused_priority": round(base, 2),
            "feedback_adjustment": round(adjustment, 2),
            "feedback_confidence": round(confidence, 2),
            "final_priority": round(final_priority, 2),
            "reason": row.get("reason"),
            "confidence": row.get("confidence"),
            "learned_score": row.get("learned_score"),
            "adaptive_priority": row.get("adaptive_priority")
        })

    integrated.sort(
        key=lambda x: (
            x["final_priority"],
            x["feedback_confidence"]
        ),
        reverse=True
    )

    report = {
        "generated_at": now(),
        "integrated_priorities": integrated,
        "top_action": integrated[0]["action"] if integrated else None,
        "top_priority": integrated[0]["final_priority"] if integrated else None,
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
        "last_integrated_at": now(),
        "action_count": len(integrated),
        "top_action": report["top_action"],
        "top_priority": report["top_priority"]
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "action_count": len(integrated)
    })

    return {
        "success": True,
        "status": "feedback_priority_integration_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "feedback_priority_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "integrate":
        result = integrate()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["integrate", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
