#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "action_queue_config.json"
STATE = MEM / "action_queue_state.json"
REPORT = MEM / "action_queue_report.json"
HEALTH = MEM / "action_queue_health.json"

PREFLIGHT = MEM / "preflight_gate_report.json"
MISSION = MEM / "mission_control_brief.json"
GOALS = MEM / "goal_strategy_goals.json"
OUTCOMES = MEM / "outcome_tracker_report.json"
GH_INTEL = MEM / "github_intelligence_report.json"

ACTION_MAP = {
    "refresh-priorities": ["python", "companyos/priorityctl", "rank"],
    "refresh-decisions": ["python", "companyos/decisionctl", "prepare"],
    "refresh-forecast": ["python", "companyos/forecastctl", "forecast"],
    "refresh-brief": ["python", "companyos/briefctl", "generate"],
    "refresh-goals": ["python", "companyos/goalctl", "generate"],
    "run-learning": ["python", "companyos/learningctl", "learn"],
    "run-health": ["python", "companyos/healthctl", "run"],
    "run-readiness": ["python", "companyos/readinessctl", "check"],
    "run-outcomes": ["python", "companyos/outcomectl", "measure"]
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

def run(command: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=300
        )
        return {
            "success": proc.returncode == 0,
            "return_code": proc.returncode,
            "stdout": proc.stdout[-2500:],
            "stderr": proc.stderr[-1200:]
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}

def build_queue() -> list[dict[str, Any]]:
    preflight = load(PREFLIGHT, {})
    mission = load(MISSION, {})
    goals = load(GOALS, {}).get("goals", [])
    outcomes = load(OUTCOMES, {})
    gh = load(GH_INTEL, {})

    queue: list[dict[str, Any]] = []

    if preflight.get("decision") == "blocked":
        queue.append({
            "action": "run-health",
            "priority": 95,
            "reason": "Preflight is blocked; verify system health before further work."
        })

    attention = mission.get("attention", [])
    if attention and attention != ["All monitored systems are operating normally."]:
        queue.append({
            "action": "run-readiness",
            "priority": 90,
            "reason": "Mission control reports items requiring attention."
        })

    needs_attention = outcomes.get("needs_attention", [])
    if needs_attention:
        queue.append({
            "action": "run-learning",
            "priority": 85,
            "reason": f"{len(needs_attention)} goal outcome(s) need attention."
        })
        queue.append({
            "action": "refresh-goals",
            "priority": 80,
            "reason": "Refresh goals after learning from underperforming outcomes."
        })

    if goals:
        queue.append({
            "action": "refresh-forecast",
            "priority": 70,
            "reason": "Keep forecast aligned with active goals."
        })

    if "uncommitted_changes" in gh.get("signals", []):
        queue.append({
            "action": "refresh-brief",
            "priority": 65,
            "reason": "Summarize current repository state before owner review."
        })

    queue.extend([
        {
            "action": "refresh-priorities",
            "priority": 60,
            "reason": "Maintain current executive ordering."
        },
        {
            "action": "refresh-decisions",
            "priority": 55,
            "reason": "Keep CEO decision queue synchronized."
        },
        {
            "action": "run-outcomes",
            "priority": 50,
            "reason": "Refresh measurable outcomes for the feedback loop."
        }
    ])

    seen = set()
    deduped = []
    for item in sorted(queue, key=lambda x: int(x["priority"]), reverse=True):
        if item["action"] in seen:
            continue
        seen.add(item["action"])
        deduped.append(item)

    return deduped

def coordinate() -> dict[str, Any]:
    cfg = load(CFG, {})
    if not cfg.get("enabled", True):
        return {"success": False, "status": "action_queue_coordinator_disabled"}

    queue = build_queue()
    minimum = int(cfg.get("minimum_priority_score", 50))
    maximum = int(cfg.get("maximum_actions_per_cycle", 10))

    selected = [x for x in queue if int(x.get("priority", 0)) >= minimum][:maximum]
    results = []

    for item in selected:
        command = ACTION_MAP.get(item["action"])
        if not command:
            results.append({
                "action": item["action"],
                "success": False,
                "error": "action_not_mapped"
            })
            continue

        result = run(command)
        results.append({
            "action": item["action"],
            "priority": item["priority"],
            "reason": item["reason"],
            "result": result,
            "success": result.get("success", False)
        })

    failures = [x for x in results if not x.get("success")]

    report = {
        "generated_at": now(),
        "queue": queue,
        "selected": selected,
        "results": results,
        "failure_count": len(failures),
        "automatic_external_write": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "generated_at": now(),
        "queued_count": len(queue),
        "executed_count": len(results),
        "failure_count": len(failures)
    })
    save(HEALTH, {
        "healthy": len(failures) == 0,
        "last_run_at": now(),
        "queued_count": len(queue),
        "executed_count": len(results),
        "failure_count": len(failures)
    })

    return {
        "success": len(failures) == 0,
        "status": "action_queue_cycle_complete",
        "report": report
    }

def status() -> dict[str, Any]:
    return {
        "success": True,
        "status": "action_queue_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    if action == "run":
        result = coordinate()
    elif action == "status":
        result = status()
    else:
        result = {
            "success": False,
            "status": "unknown_action",
            "allowed": ["run", "status"]
        }

    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
