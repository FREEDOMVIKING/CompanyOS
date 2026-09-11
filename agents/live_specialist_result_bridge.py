#!/usr/bin/env python3
import json, sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.home() / "companyos"
MEM = ROOT / "ceo_memory"

CFG = MEM / "live_result_bridge_config.json"
SOURCE = MEM / "specialist_runtime_results.json"
TARGET = MEM / "specialist_work_results.json"

STATE = MEM / "live_result_bridge_state.json"
REPORT = MEM / "live_result_bridge_report.json"
HEALTH = MEM / "live_result_bridge_health.json"

def now():
    return datetime.now(timezone.utc).isoformat()

def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save(path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)

def num(value, default=0):
    try:
        return float(value)
    except Exception:
        return float(default)

def integrate():
    cfg = load(CFG, {})
    source_rows = load(SOURCE, {}).get("results", [])
    target_doc = load(TARGET, {"results": []})
    target_rows = target_doc.get("results", [])

    existing = {
        row.get("result_id") or row.get("work_id")
        for row in target_rows
        if row.get("result_id") or row.get("work_id")
    }

    maximum = int(cfg.get("maximum_results_per_cycle", 20))
    minimum = num(cfg.get("minimum_confidence", 0.5), 0.5)

    added = []
    rejected = []

    for row in source_rows:
        if len(added) >= maximum:
            break

        if row.get("status") != "completed":
            continue

        work_id = row.get("work_id")
        result_id = f"{work_id}-result" if work_id else None

        if not work_id or result_id in existing or work_id in existing:
            continue

        actual = row.get("actual_result")
        if not isinstance(actual, dict):
            rejected.append({
                "work_id": work_id,
                "reason": "missing_structured_actual_result"
            })
            continue

        confidence = num(actual.get("confidence", 0), 0)
        if confidence < minimum:
            rejected.append({
                "work_id": work_id,
                "reason": "confidence_below_threshold",
                "confidence": confidence
            })
            continue

        integrated = {
            "result_id": result_id,
            "work_id": work_id,
            "plan_id": row.get("plan_id"),
            "decision_id": row.get("decision_id"),
            "opportunity_id": row.get("opportunity_id"),
            "title": row.get("title"),
            "specialist_role": row.get("specialist_role"),
            "specialist": row.get("specialist"),
            "work_mode": row.get("action_type"),
            "status": "completed",
            "actual_result": {
                "summary": actual.get("summary"),
                "findings": actual.get("findings", []),
                "recommendations": actual.get("recommendations", []),
                "risks": actual.get("risks", []),
                "next_internal_actions": actual.get("next_internal_actions", []),
                "confidence": confidence
            },
            "execution_boundary": "internal_non_destructive_only",
            "completed_at": row.get("completed_at") or now(),
            "integrated_at": now()
        }

        target_rows.append(integrated)
        added.append(integrated)
        existing.add(result_id)

    save(TARGET, {
        "generated_at": now(),
        "result_count": len(target_rows),
        "results": target_rows
    })

    report = {
        "generated_at": now(),
        "added_count": len(added),
        "rejected_count": len(rejected),
        "total_result_count": len(target_rows),
        "added": added,
        "rejected": rejected,
        "automatic_external_write": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
        "automatic_spending": False,
        "automatic_fund_transfer": False,
        "automatic_code_changes": False,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_destructive_actions": False
    }

    save(REPORT, report)
    save(STATE, {
        "last_integrated_at": now(),
        "added_count": len(added),
        "rejected_count": len(rejected),
        "total_result_count": len(target_rows)
    })
    save(HEALTH, {
        "healthy": True,
        "last_checked_at": now(),
        "total_result_count": len(target_rows)
    })

    return {
        "success": True,
        "status": "live_specialist_result_bridge_complete",
        "report": report
    }

def status():
    return {
        "success": True,
        "status": "live_specialist_result_bridge_status",
        "state": load(STATE, {}),
        "health": load(HEALTH, {}),
        "report": load(REPORT, {})
    }

action = sys.argv[1] if len(sys.argv) > 1 else "status"

if action == "integrate":
    result = integrate()
elif action == "status":
    result = status()
else:
    result = {
        "success": False,
        "status": "unknown_action",
        "allowed": ["integrate", "status"]
    }

print(json.dumps(result, indent=2))
raise SystemExit(0 if result.get("success") else 1)
