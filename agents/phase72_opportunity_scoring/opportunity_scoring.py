import json
from datetime import datetime, timezone

from agents.phase65_opportunity_pipeline.opportunity_pipeline import load as load_opportunities

def now():
    return datetime.now(timezone.utc).isoformat()

WEIGHTS = {
    "market_need": 0.25,
    "speed_to_revenue": 0.20,
    "automation_potential": 0.20,
    "competition_advantage": 0.15,
    "execution_feasibility": 0.20,
}

def score_factors(factors):
    normalized = {}
    total = 0.0
    for key, weight in WEIGHTS.items():
        value = max(0, min(100, int(factors.get(key, 0))))
        normalized[key] = value
        total += value * weight
    return round(total, 2), normalized

def evaluate(opportunity_id, factors):
    data = load_opportunities()
    opportunity = next(
        (x for x in data.get("opportunities", []) if x.get("opportunity_id") == opportunity_id),
        None,
    )
    if not opportunity:
        return {
            "success": False,
            "status": "phase72_opportunity_not_found",
            "opportunity_id": opportunity_id,
        }

    score, normalized = score_factors(factors)
    return {
        "success": True,
        "status": "phase72_opportunity_scored",
        "opportunity_id": opportunity_id,
        "title": opportunity.get("title"),
        "score": score,
        "factors": normalized,
        "recommendation": (
            "advance" if score >= 70 else
            "validate_more" if score >= 50 else
            "deprioritize"
        ),
        "evaluated_at": now(),
    }

def status():
    return {
        "success": True,
        "status": "phase72_opportunity_scoring_status",
        "weights": WEIGHTS,
    }

if __name__ == "__main__":
    print(json.dumps(status(), indent=2))
