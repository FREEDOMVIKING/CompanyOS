#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "opportunity_portfolio_config.json"
RERANK = MEM / "opportunity_rerank_report.json"

STATE = MEM / "opportunity_portfolio_state.json"
REPORT = MEM / "opportunity_portfolio_report.json"
HEALTH = MEM / "opportunity_portfolio_health.json"
PORTFOLIO = MEM / "active_opportunity_portfolio.json"

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

def allocate() -> dict[str, Any]:
    cfg = load(CFG, {})
    rows = load(RERANK, {}).get("reranked_opportunities", [])

    maximum = int(cfg.get("maximum_active_opportunities", 5))
    minimum = float(cfg.get("minimum_final_score", 50))
    diversify = bool(cfg.get("diversify_by_category", True))

    eligible = []
    for row in rows:
        try:
            score = float(row.get("final_opportunity_score", 0))
        except Exception:
            score = 0.0

        if score >= minimum:
            eligible.append(row)

    eligible.sort(
        key=lambda x: float(x.get("final_opportunity_score", 0)),
        reverse=True
    )

    selected = []
    used_categories = set()

    if diversify:
        for row in eligible:
            category = row.get("category") or "uncategorized"
            if category in used_categories:
                continue
            selected.append(row)
            used_categories.add(category)
            if len(selected) >= maximum:
                break

    if len(selected) < maximum:
        selected_ids = {str(x.get("id")) for x in selected}
        for row in eligible:
            if str(row.get("id")) in selected_ids:
                continue
            selected.append(row)
            if len(selected) >= maximum:
                break

    active = []
    for index, row in enumerate(selected, start=1):
        active.append({
            "portfolio_rank": index,
            "id": row.get("id"),
            "title": row.get("title"),
            "category": row.get("category"),
            "final_opportunity_score": row.get("final_opportunity_score"),
            "learning_samples": row.get("learning_samples"),
            "learning_active": row.get("learning_active"),
            "status": "active_candidate"
        })

    payload = {
        "generated_at": now(),
        "active_count": len(active),
        "opportunities": active
    }
    save(PORTFOLIO, payload)

    report = {
        "generated_at": now(),
        "eligible_count": len(eligible),
        "selected_count": len(active),
        "active_portfolio": active,
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
        "last_allocated_at": now(),
        "eligible_count": len(eligible),
        "selected_count": len(active),
        "top_opportunity": active[0]["title"] if active else None
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "selected_count": len(active)
    })

    return {
        "success": True,
        "status": "opportunity_portfolio_allocation_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "opportunity_portfolio_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {}),
        "portfolio": load(PORTFOLIO, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "allocate":
        result = allocate()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["allocate", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
