#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "strategic_alignment_config.json"
OPPS = MEM / "opportunity_discovery_results.json"
STRATEGY = MEM / "strategic_orchestrator_report.json"
PRIORITIES = MEM / "feedback_priority_report.json"
FORECAST = MEM / "business_forecasting_report.json"

STATE = MEM / "strategic_alignment_state.json"
REPORT = MEM / "strategic_alignment_report.json"
HEALTH = MEM / "strategic_alignment_health.json"

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

def clamp(v: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, v))

def normalize_opportunities(doc: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("opportunities", "results", "items"):
        value = doc.get(key)
        if isinstance(value, list):
            return value
    return []

def score_opportunity(
    opp: dict[str, Any],
    goal_signal: float,
    priority_signal: float,
    forecast_signal: float,
    cfg: dict[str, Any]
) -> float:
    raw = opp.get(
        "score",
        opp.get(
            "opportunity_score",
            opp.get("priority", 50)
        )
    )
    try:
        base = float(raw)
    except Exception:
        base = 50.0

    gw = float(cfg.get("goal_weight", 0.40))
    pw = float(cfg.get("priority_weight", 0.35))
    fw = float(cfg.get("forecast_weight", 0.25))
    total = gw + pw + fw
    if total <= 0:
        gw, pw, fw, total = 0.40, 0.35, 0.25, 1.0

    strategic = (
        goal_signal * gw +
        priority_signal * pw +
        forecast_signal * fw
    ) / total

    return clamp((base * 0.50) + (strategic * 0.50))

def align() -> dict[str, Any]:
    cfg = load(CFG, {})
    opp_doc = load(OPPS, {})
    strategy = load(STRATEGY, {})
    priority_doc = load(PRIORITIES, {})
    forecast = load(FORECAST, {})

    opportunities = normalize_opportunities(opp_doc)
    max_opps = int(cfg.get("maximum_opportunities", 20))
    minimum = float(cfg.get("minimum_alignment_score", 50))

    eligible_goals = strategy.get("eligible_goals", [])
    goal_signal = 50.0
    if eligible_goals:
        goal_scores = []
        for g in eligible_goals:
            try:
                goal_scores.append(float(g.get("score", 50)))
            except Exception:
                pass
        if goal_scores:
            goal_signal = sum(goal_scores) / len(goal_scores)

    priorities = priority_doc.get("integrated_priorities", [])
    priority_signal = 50.0
    if priorities:
        vals = []
        for p in priorities[:10]:
            try:
                vals.append(float(p.get("final_priority", 50)))
            except Exception:
                pass
        if vals:
            priority_signal = sum(vals) / len(vals)

    forecast_signal = 50.0
    if isinstance(forecast, dict):
        for key in ("confidence", "forecast_confidence", "score", "health_score"):
            if key in forecast:
                try:
                    val = float(forecast[key])
                    forecast_signal = val * 100 if 0 <= val <= 1 else val
                    break
                except Exception:
                    pass

    aligned = []

    for idx, opp in enumerate(opportunities[:max_opps], start=1):
        score = score_opportunity(
            opp,
            goal_signal,
            priority_signal,
            forecast_signal,
            cfg
        )

        aligned.append({
            "rank": idx,
            "id": opp.get("id"),
            "title": opp.get("title") or opp.get("name"),
            "category": opp.get("category"),
            "alignment_score": round(score, 2),
            "eligible": score >= minimum,
            "source": opp.get("source"),
            "recommendation": opp.get("recommendation"),
            "original": opp
        })

    aligned.sort(
        key=lambda x: x["alignment_score"],
        reverse=True
    )

    for i, item in enumerate(aligned, start=1):
        item["rank"] = i

    eligible = [x for x in aligned if x["eligible"]]

    report = {
        "generated_at": now(),
        "goal_signal": round(goal_signal, 2),
        "priority_signal": round(priority_signal, 2),
        "forecast_signal": round(forecast_signal, 2),
        "aligned_opportunities": aligned,
        "eligible_opportunities": eligible,
        "eligible_count": len(eligible),
        "top_opportunity": eligible[0]["title"] if eligible else None,
        "automatic_external_write": False,
        "automatic_code_changes": False,
        "automatic_git_reset": False,
        "automatic_git_clean": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_aligned_at": now(),
        "opportunity_count": len(aligned),
        "eligible_count": len(eligible),
        "top_opportunity": report["top_opportunity"]
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "opportunity_count": len(aligned),
        "eligible_count": len(eligible)
    })

    return {
        "success": True,
        "status": "strategic_opportunity_alignment_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "strategic_opportunity_alignment_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "align":
        result = align()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["align", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
