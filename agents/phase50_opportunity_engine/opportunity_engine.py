#!/usr/bin/env python3

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "ceo_memory/phase50/phase50_config.json"
STATE = ROOT / "ceo_memory/phase50/phase50_state.json"
OPPORTUNITIES = ROOT / "ceo_memory/phase50/opportunities.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def opportunity_id(data):
    raw = "|".join([
        str(data.get("name", "")).strip().lower(),
        str(data.get("market", "")).strip().lower(),
        str(data.get("source", "")).strip().lower()
    ])
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def score_opportunity(opportunity, config):
    scoring = config.get("scoring", {})

    total = 0
    breakdown = {}

    for category, weight in scoring.items():
        value = opportunity.get("scores", {}).get(category, 0)

        try:
            value = max(0, min(100, float(value)))
        except (TypeError, ValueError):
            value = 0

        weighted = (value / 100.0) * float(weight)
        breakdown[category] = round(weighted, 2)
        total += weighted

    return round(total, 2), breakdown


def qualify(opportunity, config):
    score, breakdown = score_opportunity(opportunity, config)

    confidence = opportunity.get("confidence_score", 0)

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0

    qualified = (
        score >= config.get("minimum_qualification_score", 65)
        and confidence >= config.get("minimum_confidence_score", 60)
    )

    return {
        **opportunity,
        "opportunity_id": opportunity_id(opportunity),
        "qualification_score": score,
        "score_breakdown": breakdown,
        "qualified": qualified,
        "evaluated_at": now()
    }


def process(opportunities):
    config = load_json(CONFIG, {})
    existing = load_json(OPPORTUNITIES, {"opportunities": []})

    known = {
        x.get("opportunity_id")
        for x in existing.get("opportunities", [])
    }

    results = []

    for opportunity in opportunities:
        result = qualify(opportunity, config)

        if result["opportunity_id"] in known:
            result["duplicate"] = True
        else:
            result["duplicate"] = False
            existing.setdefault("opportunities", []).append(result)
            known.add(result["opportunity_id"])

        results.append(result)

    save_json(OPPORTUNITIES, existing)

    state = {
        "last_run_at": now(),
        "opportunities_processed": len(results),
        "qualified": sum(1 for x in results if x["qualified"]),
        "duplicates": sum(1 for x in results if x["duplicate"])
    }

    save_json(STATE, state)

    return {
        "success": True,
        "status": "phase50_opportunities_processed",
        "state": state,
        "results": results
    }


def status():
    return {
        "success": True,
        "status": "phase50_opportunity_engine_status",
        "config": load_json(CONFIG, {}),
        "state": load_json(
            STATE,
            {
                "last_run_at": None,
                "opportunities_processed": 0,
                "qualified": 0,
                "duplicates": 0
            }
        ),
        "opportunities": load_json(
            OPPORTUNITIES,
            {"opportunities": []}
        )
    }


if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
