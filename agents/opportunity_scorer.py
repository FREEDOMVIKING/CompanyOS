#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG_PATH = MEMORY / "opportunity_scoring_config.json"
OPPORTUNITIES_PATH = MEMORY / "discovered_opportunities.json"
RANKINGS_PATH = MEMORY / "opportunity_rankings.json"
HEALTH_PATH = MEMORY / "opportunity_scoring_health.json"
AUDIT_PATH = MEMORY / "opportunity_scoring_audit.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    temporary.replace(path)


def clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return max(minimum, min(maximum, value))


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT_PATH, [])

    if not isinstance(records, list):
        records = []

    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })

    save_json(AUDIT_PATH, records[-500:])


def recurring_revenue_score(revenue_model: str) -> int:
    value = revenue_model.lower()

    if "subscription" in value:
        return 95

    if "support plan" in value:
        return 88

    if "setup fee" in value and "monthly" in value:
        return 90

    if "revenue share" in value:
        return 75

    if "premium" in value:
        return 68

    if "one-time" in value or "one time" in value:
        return 45

    return 55


def competition_score(opportunity: dict[str, Any]) -> int:
    category = str(opportunity.get("category", ""))

    base_scores = {
        "local_services": 84,
        "operations": 80,
        "small_business_tools": 74,
        "digital_products": 68,
        "developer_tools": 62,
        "ai_automation": 58,
    }

    score = base_scores.get(category, 60)

    strategic_fit = int(opportunity.get("strategic_fit", 50))
    demand = int(opportunity.get("estimated_market_demand", 50))

    if strategic_fit >= 90:
        score += 6

    if demand >= 80:
        score -= 4

    return round(clamp(score))


def execution_confidence_score(opportunity: dict[str, Any]) -> int:
    effort = int(opportunity.get("estimated_build_effort", 100))
    strategic_fit = int(opportunity.get("strategic_fit", 50))

    effort_score = clamp(110 - effort)
    confidence = effort_score * 0.55 + strategic_fit * 0.45

    return round(clamp(confidence))


def speed_to_launch_score(opportunity: dict[str, Any]) -> int:
    effort = int(opportunity.get("estimated_build_effort", 100))

    score = 110 - effort

    if effort <= 30:
        score += 8
    elif effort >= 65:
        score -= 8

    return round(clamp(score))


def risk_score(opportunity: dict[str, Any]) -> int:
    effort = int(opportunity.get("estimated_build_effort", 100))
    demand = int(opportunity.get("estimated_market_demand", 50))
    revenue = int(opportunity.get("estimated_revenue_potential", 50))

    build_risk = effort
    demand_risk = 100 - demand
    revenue_risk = 100 - revenue

    risk = (
        build_risk * 0.45
        + demand_risk * 0.30
        + revenue_risk * 0.25
    )

    return round(clamp(risk))


def risk_level(risk: int) -> str:
    if risk <= 30:
        return "low"

    if risk <= 50:
        return "moderate"

    if risk <= 70:
        return "high"

    return "very_high"


def effort_level(effort: int) -> str:
    if effort <= 30:
        return "low"

    if effort <= 50:
        return "moderate"

    if effort <= 70:
        return "high"

    return "very_high"


def launch_window(speed: int) -> str:
    if speed >= 80:
        return "1-2 weeks"

    if speed >= 65:
        return "2-4 weeks"

    if speed >= 50:
        return "1-2 months"

    return "2+ months"


def calculate_weighted_score(
    opportunity: dict[str, Any],
    weights: dict[str, float],
) -> dict[str, Any]:
    market_demand = int(
        opportunity.get("estimated_market_demand", 0)
    )
    revenue_potential = int(
        opportunity.get("estimated_revenue_potential", 0)
    )
    strategic_fit = int(
        opportunity.get("strategic_fit", 0)
    )
    effort = int(
        opportunity.get("estimated_build_effort", 100)
    )

    speed = speed_to_launch_score(opportunity)
    recurring = recurring_revenue_score(
        str(opportunity.get("revenue_model", ""))
    )
    competition = competition_score(opportunity)
    execution = execution_confidence_score(opportunity)
    risk = risk_score(opportunity)
    low_risk = 100 - risk

    factors = {
        "market_demand": market_demand,
        "revenue_potential": revenue_potential,
        "strategic_fit": strategic_fit,
        "speed_to_launch": speed,
        "recurring_revenue": recurring,
        "competition_advantage": competition,
        "execution_confidence": execution,
        "low_risk": low_risk,
    }

    score = 0.0

    for key, factor_value in factors.items():
        score += factor_value * float(weights.get(key, 0))

    score = round(clamp(score), 2)

    confidence = round(
        clamp(
            (
                strategic_fit
                + execution
                + competition
                + market_demand
            ) / 4
        ),
        2,
    )

    return {
        "priority_score": score,
        "confidence_score": confidence,
        "risk_score": risk,
        "risk_level": risk_level(risk),
        "effort_level": effort_level(effort),
        "speed_to_launch_score": speed,
        "estimated_launch_window": launch_window(speed),
        "recurring_revenue_score": recurring,
        "competition_advantage_score": competition,
        "execution_confidence_score": execution,
        "factors": factors,
    }


def recommendation_status(
    score: float,
    qualified_threshold: float,
    recommended_threshold: float,
) -> str:
    if score >= recommended_threshold:
        return "recommended"

    if score >= qualified_threshold:
        return "qualified"

    return "rejected"


def strategic_reasons(
    opportunity: dict[str, Any],
    scoring: dict[str, Any],
) -> list[str]:
    reasons: list[str] = []

    if int(opportunity.get("strategic_fit", 0)) >= 90:
        reasons.append("Strong fit with current CompanyOS capabilities")

    if int(opportunity.get("estimated_market_demand", 0)) >= 75:
        reasons.append("High estimated market demand")

    if int(opportunity.get("estimated_revenue_potential", 0)) >= 75:
        reasons.append("Strong revenue potential")

    if scoring["recurring_revenue_score"] >= 85:
        reasons.append("Recurring-income business model")

    if scoring["speed_to_launch_score"] >= 75:
        reasons.append("Fast path to a usable first version")

    if scoring["risk_level"] == "low":
        reasons.append("Low estimated execution risk")

    if scoring["competition_advantage_score"] >= 80:
        reasons.append("Strong niche or operational advantage")

    if not reasons:
        reasons.append("Meets minimum opportunity qualification criteria")

    return reasons[:5]


def score_all() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "opportunity_scoring_disabled",
        }
        audit("score", result)
        return result

    source = load_json(OPPORTUNITIES_PATH, {})
    opportunities = source.get("opportunities", [])

    if not opportunities:
        result = {
            "success": False,
            "status": "no_opportunities_available",
            "next_command": "python companyos/opportunityctl scan",
        }
        audit("score", result)
        return result

    weights = config.get("weights", {})
    qualified_threshold = float(
        config.get("minimum_qualified_score", 60)
    )
    recommended_threshold = float(
        config.get("minimum_recommended_score", 72)
    )
    maximum_recommended = int(
        config.get("maximum_recommended_opportunities", 5)
    )

    rankings: list[dict[str, Any]] = []

    for opportunity in opportunities:
        scoring = calculate_weighted_score(opportunity, weights)

        status = recommendation_status(
            scoring["priority_score"],
            qualified_threshold,
            recommended_threshold,
        )

        ranking = {
            "opportunity_id": opportunity.get("id"),
            "title": opportunity.get("title"),
            "category": opportunity.get("category"),
            "target_customer": opportunity.get("target_customer"),
            "revenue_model": opportunity.get("revenue_model"),
            "priority_score": scoring["priority_score"],
            "confidence_score": scoring["confidence_score"],
            "recommendation": status,
            "risk_score": scoring["risk_score"],
            "risk_level": scoring["risk_level"],
            "effort_level": scoring["effort_level"],
            "estimated_launch_window": (
                scoring["estimated_launch_window"]
            ),
            "market_demand": opportunity.get(
                "estimated_market_demand"
            ),
            "revenue_potential": opportunity.get(
                "estimated_revenue_potential"
            ),
            "strategic_fit": opportunity.get("strategic_fit"),
            "speed_to_launch_score": (
                scoring["speed_to_launch_score"]
            ),
            "recurring_revenue_score": (
                scoring["recurring_revenue_score"]
            ),
            "competition_advantage_score": (
                scoring["competition_advantage_score"]
            ),
            "execution_confidence_score": (
                scoring["execution_confidence_score"]
            ),
            "reasons": strategic_reasons(
                opportunity,
                scoring,
            ),
            "owner_approval_required": True,
            "scored_at": now(),
        }

        rankings.append(ranking)

        opportunity["priority_score"] = scoring["priority_score"]
        opportunity["confidence_score"] = scoring["confidence_score"]
        opportunity["risk_score"] = scoring["risk_score"]
        opportunity["risk_level"] = scoring["risk_level"]
        opportunity["recommendation"] = status
        opportunity["estimated_launch_window"] = (
            scoring["estimated_launch_window"]
        )
        opportunity["last_scored_at"] = now()
        opportunity["updated_at"] = now()

    rankings.sort(
        key=lambda item: (
            float(item.get("priority_score", 0)),
            float(item.get("confidence_score", 0)),
        ),
        reverse=True,
    )

    for index, ranking in enumerate(rankings, start=1):
        ranking["rank"] = index

    recommended = [
        item
        for item in rankings
        if item.get("recommendation") == "recommended"
    ][:maximum_recommended]

    qualified_count = sum(
        1
        for item in rankings
        if item.get("recommendation") in {
            "qualified",
            "recommended",
        }
    )

    recommended_count = sum(
        1
        for item in rankings
        if item.get("recommendation") == "recommended"
    )

    rejected_count = sum(
        1
        for item in rankings
        if item.get("recommendation") == "rejected"
    )

    best = rankings[0] if rankings else None

    ranking_store = {
        "schema_version": 1,
        "rankings": rankings,
        "best_opportunity": best,
        "recommended_opportunities": recommended,
        "statistics": {
            "total_scored": len(rankings),
            "qualified": qualified_count,
            "recommended": recommended_count,
            "rejected": rejected_count,
        },
        "owner_approval_required": True,
        "automatic_selection": False,
        "automatic_project_creation": False,
        "last_scored_at": now(),
    }

    save_json(RANKINGS_PATH, ranking_store)
    save_json(OPPORTUNITIES_PATH, source)

    health = {
        "healthy": True,
        "last_scored_at": ranking_store["last_scored_at"],
        "last_error": None,
        "total_scored": len(rankings),
        "best_opportunity_id": (
            best.get("opportunity_id") if best else None
        ),
    }

    save_json(HEALTH_PATH, health)

    result = {
        "success": True,
        "status": "opportunity_scoring_complete",
        "total_scored": len(rankings),
        "qualified": qualified_count,
        "recommended": recommended_count,
        "rejected": rejected_count,
        "best_opportunity": best,
        "top_rankings": rankings[:5],
        "automatic_selection": False,
        "automatic_project_creation": False,
        "owner_approval_required": True,
    }

    audit("score", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})
    ranking_store = load_json(RANKINGS_PATH, {})
    health = load_json(HEALTH_PATH, {})

    result = {
        "success": True,
        "status": "opportunity_scoring_status",
        "enabled": config.get("enabled", False),
        "healthy": health.get("healthy", False),
        "last_scored_at": ranking_store.get("last_scored_at"),
        "statistics": ranking_store.get("statistics", {}),
        "best_opportunity": ranking_store.get("best_opportunity"),
        "automatic_scoring": config.get(
            "automatic_scoring",
            False,
        ),
        "automatic_selection": config.get(
            "automatic_selection",
            False,
        ),
        "automatic_project_creation": config.get(
            "automatic_project_creation",
            False,
        ),
        "owner_approval_required": config.get(
            "owner_approval_required",
            True,
        ),
    }

    audit("status", result)
    return result


def list_rankings(limit: int = 20) -> dict[str, Any]:
    store = load_json(RANKINGS_PATH, {})
    rankings = store.get("rankings", [])

    limit = max(1, min(limit, 100))

    result = {
        "success": True,
        "status": "opportunity_ranking_list",
        "count": min(limit, len(rankings)),
        "total": len(rankings),
        "rankings": [
            {
                "rank": item.get("rank"),
                "opportunity_id": item.get("opportunity_id"),
                "title": item.get("title"),
                "priority_score": item.get("priority_score"),
                "recommendation": item.get("recommendation"),
                "risk_level": item.get("risk_level"),
                "effort_level": item.get("effort_level"),
                "estimated_launch_window": item.get(
                    "estimated_launch_window"
                ),
            }
            for item in rankings[:limit]
        ],
    }

    audit("list", result)
    return result


def show(item_id: str) -> dict[str, Any]:
    store = load_json(RANKINGS_PATH, {})

    for ranking in store.get("rankings", []):
        if ranking.get("opportunity_id") == item_id:
            result = {
                "success": True,
                "status": "opportunity_ranking_details",
                "ranking": ranking,
            }
            audit("show", result)
            return result

    result = {
        "success": False,
        "status": "opportunity_ranking_not_found",
        "opportunity_id": item_id,
    }

    audit("show", result)
    return result


def best() -> dict[str, Any]:
    store = load_json(RANKINGS_PATH, {})
    best_opportunity = store.get("best_opportunity")

    result = {
        "success": bool(best_opportunity),
        "status": (
            "best_opportunity_selected"
            if best_opportunity
            else "best_opportunity_unavailable"
        ),
        "best_opportunity": best_opportunity,
        "selection_is_recommendation_only": True,
        "owner_approval_required": True,
    }

    audit("best", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: opportunity_scorer.py "
            "score|status|list [limit]|show <id>|best"
        )
        return 2

    action = sys.argv[1].lower()

    try:
        if action == "score":
            return print_result(score_all())

        if action == "status":
            return print_result(status())

        if action == "list":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            return print_result(list_rankings(limit))

        if action == "show":
            if len(sys.argv) < 3:
                raise ValueError("Opportunity ID is required")
            return print_result(show(sys.argv[2]))

        if action == "best":
            return print_result(best())

        return print_result({
            "success": False,
            "status": "unknown_scoring_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "opportunity_scoring_error",
            "action": action,
            "error": str(exc),
        }

        save_json(
            HEALTH_PATH,
            {
                "healthy": False,
                "last_checked_at": now(),
                "last_error": str(exc),
            },
        )

        audit("error", result)
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
