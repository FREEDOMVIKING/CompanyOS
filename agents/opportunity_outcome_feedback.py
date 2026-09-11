#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "opportunity_outcome_config.json"
EXEC = MEM / "opportunity_executor_report.json"

STATE = MEM / "opportunity_outcome_state.json"
REPORT = MEM / "opportunity_outcome_report.json"
HEALTH = MEM / "opportunity_outcome_health.json"
SCORES = MEM / "opportunity_action_scores.json"

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

def analyze() -> dict[str, Any]:
    cfg = load(CFG, {})
    execution = load(EXEC, {})
    store = load(SCORES, {"schema_version": 1, "actions": {}})
    actions = store.setdefault("actions", {})

    success_reward = float(cfg.get("success_reward", 5))
    failure_penalty = float(cfg.get("failure_penalty", 10))
    blocked_penalty = float(cfg.get("blocked_penalty", 1))
    minimum_samples = int(cfg.get("minimum_samples_before_learning", 2))

    updates = []

    for row in execution.get("results", []):
        action_id = row.get("action_id")
        if not action_id:
            continue

        rec = actions.setdefault(action_id, {
            "score": 50.0,
            "successes": 0,
            "failures": 0,
            "blocked": 0,
            "samples": 0
        })

        if row.get("status") == "success":
            rec["score"] = min(100.0, float(rec.get("score", 50)) + success_reward)
            rec["successes"] = int(rec.get("successes", 0)) + 1
            outcome = "success"
        else:
            rec["score"] = max(0.0, float(rec.get("score", 50)) - failure_penalty)
            rec["failures"] = int(rec.get("failures", 0)) + 1
            outcome = "failure"

        rec["samples"] = int(rec.get("samples", 0)) + 1
        rec["last_updated_at"] = now()

        updates.append({
            "action_id": action_id,
            "outcome": outcome,
            "score": round(rec["score"], 2),
            "samples": rec["samples"],
            "learning_active": rec["samples"] >= minimum_samples
        })

    for row in execution.get("blocked", []):
        action_id = row.get("action_id")
        if not action_id:
            continue

        rec = actions.setdefault(action_id, {
            "score": 50.0,
            "successes": 0,
            "failures": 0,
            "blocked": 0,
            "samples": 0
        })

        rec["score"] = max(0.0, float(rec.get("score", 50)) - blocked_penalty)
        rec["blocked"] = int(rec.get("blocked", 0)) + 1
        rec["samples"] = int(rec.get("samples", 0)) + 1
        rec["last_updated_at"] = now()

        updates.append({
            "action_id": action_id,
            "outcome": "blocked",
            "score": round(rec["score"], 2),
            "samples": rec["samples"],
            "learning_active": rec["samples"] >= minimum_samples
        })

    store["generated_at"] = now()
    save(SCORES, store)

    ranked = sorted(
        (
            {
                "action_id": aid,
                "score": round(float(data.get("score", 0)), 2),
                "successes": int(data.get("successes", 0)),
                "failures": int(data.get("failures", 0)),
                "blocked": int(data.get("blocked", 0)),
                "samples": int(data.get("samples", 0)),
                "learning_active": int(data.get("samples", 0)) >= minimum_samples
            }
            for aid, data in actions.items()
        ),
        key=lambda x: (x["score"], x["samples"]),
        reverse=True
    )

    report = {
        "generated_at": now(),
        "updates": updates,
        "ranked_actions": ranked,
        "top_action": ranked[0]["action_id"] if ranked else None,
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
        "last_analyzed_at": now(),
        "tracked_action_count": len(actions),
        "update_count": len(updates),
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
        "status": "opportunity_outcome_feedback_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "opportunity_outcome_feedback_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {}),
        "scores": load(SCORES, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "analyze":
        result = analyze()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["analyze", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
