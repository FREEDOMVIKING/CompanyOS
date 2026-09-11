#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "execution_outcome_learner_config.json"
EXECUTION = MEM / "plan_executor_report.json"
SCORES = MEM / "execution_action_scores.json"
STATE = MEM / "execution_outcome_learner_state.json"
REPORT = MEM / "execution_outcome_learner_report.json"
HEALTH = MEM / "execution_outcome_learner_health.json"

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

def learn() -> dict[str, Any]:
    cfg = load(CFG, {})
    execution = load(EXECUTION, {})
    score_store = load(SCORES, {"schema_version": 1, "actions": {}})
    actions = score_store.setdefault("actions", {})

    success_reward = float(cfg.get("success_reward", 6))
    failure_penalty = float(cfg.get("failure_penalty", 12))
    blocked_penalty = float(cfg.get("blocked_penalty", 2))
    gain = float(cfg.get("confidence_gain_success", 0.08))
    loss = float(cfg.get("confidence_loss_failure", 0.15))
    min_conf = float(cfg.get("minimum_confidence", 0.10))
    max_conf = float(cfg.get("maximum_confidence", 0.99))
    min_score = float(cfg.get("minimum_score", 0))
    max_score = float(cfg.get("maximum_score", 100))

    updates = []

    for item in execution.get("results", []):
        action = item.get("action")
        if not action:
            continue

        current = actions.get(action, {
            "score": 50.0,
            "confidence": 0.50,
            "successes": 0,
            "failures": 0,
            "blocked": 0
        })

        if item.get("success"):
            current["score"] = clamp(
                float(current.get("score", 50)) + success_reward,
                min_score,
                max_score
            )
            current["confidence"] = clamp(
                float(current.get("confidence", 0.5)) + gain,
                min_conf,
                max_conf
            )
            current["successes"] = int(current.get("successes", 0)) + 1
            outcome = "success"
        else:
            current["score"] = clamp(
                float(current.get("score", 50)) - failure_penalty,
                min_score,
                max_score
            )
            current["confidence"] = clamp(
                float(current.get("confidence", 0.5)) - loss,
                min_conf,
                max_conf
            )
            current["failures"] = int(current.get("failures", 0)) + 1
            outcome = "failure"

        current["last_updated_at"] = now()
        actions[action] = current
        updates.append({
            "action": action,
            "outcome": outcome,
            "score": round(current["score"], 2),
            "confidence": round(current["confidence"], 4)
        })

    for item in execution.get("blocked", []):
        action = item.get("action")
        if not action:
            continue

        current = actions.get(action, {
            "score": 50.0,
            "confidence": 0.50,
            "successes": 0,
            "failures": 0,
            "blocked": 0
        })

        current["score"] = clamp(
            float(current.get("score", 50)) - blocked_penalty,
            min_score,
            max_score
        )
        current["blocked"] = int(current.get("blocked", 0)) + 1
        current["last_updated_at"] = now()

        actions[action] = current
        updates.append({
            "action": action,
            "outcome": "blocked",
            "score": round(current["score"], 2),
            "confidence": round(float(current.get("confidence", 0.5)), 4)
        })

    score_store["generated_at"] = now()
    save(SCORES, score_store)

    ranked = sorted(
        (
            {
                "action": action,
                "score": round(float(data.get("score", 0)), 2),
                "confidence": round(float(data.get("confidence", 0)), 4),
                "successes": int(data.get("successes", 0)),
                "failures": int(data.get("failures", 0)),
                "blocked": int(data.get("blocked", 0))
            }
            for action, data in actions.items()
        ),
        key=lambda x: (x["score"] * x["confidence"], x["score"]),
        reverse=True
    )

    report = {
        "generated_at": now(),
        "updates": updates,
        "ranked_actions": ranked,
        "top_action": ranked[0]["action"] if ranked else None,
        "top_effective_score": (
            round(ranked[0]["score"] * ranked[0]["confidence"], 2)
            if ranked else None
        ),
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
        "last_learning_at": now(),
        "update_count": len(updates),
        "tracked_action_count": len(actions),
        "top_action": report["top_action"]
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "tracked_action_count": len(actions),
        "update_count": len(updates)
    })

    return {
        "success": True,
        "status": "execution_outcome_learning_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "execution_outcome_learner_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {}),
        "scores": load(SCORES, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "learn":
        result = learn()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["learn", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
