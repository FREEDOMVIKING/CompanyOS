#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "opportunity_activation_config.json"
ALIGN = MEM / "strategic_alignment_report.json"
ELIGIBILITY = MEM / "execution_eligibility_report.json"

STATE = MEM / "opportunity_activation_state.json"
REPORT = MEM / "opportunity_activation_report.json"
HEALTH = MEM / "opportunity_activation_health.json"
QUEUE = MEM / "opportunity_activation_queue.json"

CATEGORY_MAP = {
    "internal": "internal_reversible",
    "analysis": "internal_read_only",
    "research": "external_read_only",
    "customer": "customer_contact",
    "sales": "external_write",
    "publication": "publication",
    "finance": "spending"
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

def normalize_category(value: Any) -> str:
    if not value:
        return "internal_read_only"
    key = str(value).strip().lower()
    return CATEGORY_MAP.get(key, key if key in {
        "internal_read_only",
        "internal_reversible",
        "external_read_only",
        "external_write",
        "customer_contact",
        "publication",
        "spending"
    } else "internal_read_only")

def activate() -> dict[str, Any]:
    cfg = load(CFG, {})
    align = load(ALIGN, {})
    eligibility = load(ELIGIBILITY, {})

    system_ready = eligibility.get("system_ready") is True
    matrix = eligibility.get("eligibility", {})

    minimum = float(cfg.get("minimum_alignment_score", 50))
    maximum = int(cfg.get("maximum_candidates", 10))

    candidates = []
    blocked = []

    for item in align.get("eligible_opportunities", [])[:maximum]:
        score = float(item.get("alignment_score", 0))
        category = normalize_category(item.get("category"))

        if score < minimum:
            blocked.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "reason": "below_minimum_alignment_score",
                "alignment_score": score
            })
            continue

        if cfg.get("require_system_ready", True) and not system_ready:
            blocked.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "reason": "system_not_ready",
                "alignment_score": score,
                "category": category
            })
            continue

        if cfg.get("require_execution_eligibility", True) and not bool(matrix.get(category, False)):
            blocked.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "reason": "category_not_eligible",
                "alignment_score": score,
                "category": category
            })
            continue

        candidates.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "category": category,
            "alignment_score": score,
            "status": "activated",
            "source": item.get("source"),
            "recommendation": item.get("recommendation")
        })

    queue = {
        "generated_at": now(),
        "system_ready": system_ready,
        "candidates": candidates
    }
    save(QUEUE, queue)

    report = {
        "generated_at": now(),
        "system_ready": system_ready,
        "activated_count": len(candidates),
        "blocked_count": len(blocked),
        "activated": candidates,
        "blocked": blocked,
        "automatic_external_write": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_activation_at": now(),
        "system_ready": system_ready,
        "activated_count": len(candidates),
        "blocked_count": len(blocked),
        "top_candidate": candidates[0]["title"] if candidates else None
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "activated_count": len(candidates),
        "blocked_count": len(blocked)
    })

    return {
        "success": True,
        "status": "opportunity_activation_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "opportunity_activation_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {}),
        "queue": load(QUEUE, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "activate":
        result = activate()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["activate", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
