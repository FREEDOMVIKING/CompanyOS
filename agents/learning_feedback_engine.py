#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "learning_feedback_config.json"
STATE = MEMORY / "learning_feedback_state.json"
INSIGHTS = MEMORY / "learning_feedback_insights.json"
HEALTH = MEMORY / "learning_feedback_health.json"
AUDIT = MEMORY / "learning_feedback_audit.json"

DECISION_HISTORY = MEMORY / "ceo_decision_history.json"
IMPROVEMENT_BACKLOG = MEMORY / "continuous_improvement_backlog.json"
PERFORMANCE = MEMORY / "performance_analytics_report.json"
PRIORITY_CONFIG = MEMORY / "executive_priority_config.json"
GOALS = MEMORY / "goal_strategy_goals.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)


def audit(action: str, result: dict[str, Any]) -> None:
    records = load_json(AUDIT, [])
    if not isinstance(records, list):
        records = []
    records.append({
        "timestamp": now(),
        "action": action,
        "success": result.get("success", False),
        "result": result,
    })
    save_json(AUDIT, records[-1000:])


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalize(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        return weights
    return {
        key: round(value / total, 4)
        for key, value in weights.items()
    }


def learn() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {"success": False, "status": "learning_feedback_disabled"}
        audit("learn", result)
        return result

    history = load_json(DECISION_HISTORY, {}).get("history", [])
    improvements = load_json(IMPROVEMENT_BACKLOG, {}).get("items", [])
    performance = load_json(PERFORMANCE, {}).get("report", {})
    goals = load_json(GOALS, {}).get("goals", [])

    approved = sum(1 for x in history if x.get("outcome") == "approved")
    rejected = sum(1 for x in history if x.get("outcome") == "rejected")
    deferred = sum(1 for x in history if x.get("outcome") == "deferred")

    completed_improvements = sum(
        1 for x in improvements if x.get("status") == "completed"
    )
    proposed_improvements = sum(
        1 for x in improvements if x.get("status") == "proposed"
    )

    health_score = float(performance.get("health_score") or 0.0)
    active_goals = len([g for g in goals if g.get("status") == "active"])

    insights = []

    if rejected > approved:
        insights.append({
            "type": "decision_quality",
            "message": "Rejected decisions exceed approved decisions; reduce aggressiveness in priority scoring.",
            "signal": "reduce_aggressiveness",
        })

    if deferred > approved:
        insights.append({
            "type": "decision_latency",
            "message": "Deferred decisions exceed approved decisions; prioritize clearer evidence and easier execution.",
            "signal": "favor_evidence_and_ease",
        })

    if proposed_improvements > completed_improvements * 2 and proposed_improvements >= 3:
        insights.append({
            "type": "improvement_backlog",
            "message": "Improvement backlog is growing faster than completion.",
            "signal": "favor_execution_ease",
        })

    if health_score and health_score < 70:
        insights.append({
            "type": "operating_health",
            "message": "Operating health is below 70; prioritize risk reduction and execution reliability.",
            "signal": "favor_risk_reduction",
        })

    if active_goals > 7:
        insights.append({
            "type": "goal_load",
            "message": "Too many active goals may dilute execution focus.",
            "signal": "increase_urgency_weight",
        })

    priority_config = load_json(PRIORITY_CONFIG, {})
    weights = priority_config.get("weights", {})

    adjusted = False
    before = dict(weights)

    if config.get("automatic_weight_tuning", True) and weights:
        max_step = float(config.get("maximum_weight_adjustment_per_cycle", 0.05))

        for insight in insights:
            signal = insight.get("signal")

            if signal == "reduce_aggressiveness":
                weights["profitability"] = clamp(
                    float(weights.get("profitability", 0.30)) - max_step,
                    0.05,
                    0.60,
                )
                weights["evidence"] = clamp(
                    float(weights.get("evidence", 0.10)) + max_step,
                    0.05,
                    0.40,
                )

            elif signal == "favor_evidence_and_ease":
                weights["evidence"] = clamp(
                    float(weights.get("evidence", 0.10)) + max_step,
                    0.05,
                    0.40,
                )
                weights["execution_ease"] = clamp(
                    float(weights.get("execution_ease", 0.10)) + max_step,
                    0.05,
                    0.40,
                )

            elif signal == "favor_execution_ease":
                weights["execution_ease"] = clamp(
                    float(weights.get("execution_ease", 0.10)) + max_step,
                    0.05,
                    0.40,
                )

            elif signal == "favor_risk_reduction":
                weights["risk_reduction"] = clamp(
                    float(weights.get("risk_reduction", 0.20)) + max_step,
                    0.05,
                    0.50,
                )

            elif signal == "increase_urgency_weight":
                weights["urgency"] = clamp(
                    float(weights.get("urgency", 0.30)) + max_step,
                    0.05,
                    0.60,
                )

        weights = normalize({k: float(v) for k, v in weights.items()})
        adjusted = weights != before

        if adjusted:
            priority_config["weights"] = weights
            priority_config["last_learned_at"] = now()
            save_json(PRIORITY_CONFIG, priority_config)

    state = {
        "generated_at": now(),
        "decision_history_count": len(history),
        "approved_decisions": approved,
        "rejected_decisions": rejected,
        "deferred_decisions": deferred,
        "completed_improvements": completed_improvements,
        "proposed_improvements": proposed_improvements,
        "performance_health_score": health_score,
        "active_goal_count": active_goals,
        "weights_before": before,
        "weights_after": weights,
        "weights_adjusted": adjusted,
    }
    save_json(STATE, state)

    insight_payload = {
        "generated_at": now(),
        "count": len(insights),
        "insights": insights,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False,
    }
    save_json(INSIGHTS, insight_payload)

    save_json(
        HEALTH,
        {
            "healthy": True,
            "last_learned_at": now(),
            "insight_count": len(insights),
            "weights_adjusted": adjusted,
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "learning_feedback_cycle_complete",
        "state": state,
        "insights": insight_payload,
    }
    audit("learn", result)
    return result


def show() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "learning_feedback",
        "state": load_json(STATE, {}),
        "insights": load_json(INSIGHTS, {}),
    }
    audit("show", result)
    return result


def status() -> dict[str, Any]:
    result = {
        "success": True,
        "status": "learning_feedback_status",
        "config": load_json(CONFIG, {}),
        "health": load_json(HEALTH, {}),
    }
    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "learn":
            return print_result(learn())
        if action == "show":
            return print_result(show())
        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_learning_action",
            "action": action,
            "allowed": ["learn", "show", "status"],
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "learning_feedback_error",
            "error": str(exc),
        }
        save_json(
            HEALTH,
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
