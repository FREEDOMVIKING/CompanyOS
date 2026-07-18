#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "confidence_priority_config.json"
ADAPTIVE = MEM / "adaptive_priority_report.json"
LEARNED = MEM / "execution_action_scores.json"

STATE = MEM / "confidence_priority_state.json"
REPORT = MEM / "confidence_priority_report.json"
HEALTH = MEM / "confidence_priority_health.json"

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

def fuse() -> dict[str, Any]:
    cfg = load(CFG, {})
    adaptive = load(ADAPTIVE, {}).get("adaptive_priorities", [])
    learned = load(LEARNED, {}).get("actions", {})

    cw = float(cfg.get("confidence_weight", 0.35))
    lw = float(cfg.get("learned_score_weight", 0.35))
    aw = float(cfg.get("adaptive_priority_weight", 0.30))

    total = cw + lw + aw
    if total <= 0:
        cw, lw, aw, total = 0.35, 0.35, 0.30, 1.0

    fused = []

    for item in adaptive:
        action = item.get("action")
        if not action:
            continue

        adaptive_priority = float(item.get("adaptive_priority", 50))
        learned_row = learned.get(action, {})
        learned_score = float(learned_row.get("score", 50))
        confidence = float(learned_row.get("confidence", 0.50))

        confidence_percent = confidence * 100.0

        fused_priority = (
            confidence_percent * cw
            + learned_score * lw
            + adaptive_priority * aw
        ) / total

        fused_priority = clamp(
            fused_priority,
            float(cfg.get("minimum_fused_priority", 1)),
            float(cfg.get("maximum_fused_priority", 100))
        )

        fused.append({
            "action": action,
            "adaptive_priority": round(adaptive_priority, 2),
            "learned_score": round(learned_score, 2),
            "confidence": round(confidence, 4),
            "fused_priority": round(fused_priority, 2),
            "reason": item.get("reason"),
            "outcomes": item.get("outcomes", {})
        })

    fused.sort(
        key=lambda x: (
            x["fused_priority"],
            x["confidence"],
            x["learned_score"]
        ),
        reverse=True
    )

    report = {
        "generated_at": now(),
        "fused_priorities": fused,
        "top_action": fused[0]["action"] if fused else None,
        "top_fused_priority": fused[0]["fused_priority"] if fused else None,
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
        "last_fused_at": now(),
        "action_count": len(fused),
        "top_action": report["top_action"],
        "top_fused_priority": report["top_fused_priority"]
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "action_count": len(fused)
    })

    return {
        "success": True,
        "status": "confidence_priority_fusion_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "confidence_priority_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "fuse":
        result = fuse()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["fuse", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
