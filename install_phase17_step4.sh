#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase17_step4_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$BACKUP"

echo "============================================================"
echo " Phase 17 Step 4 - CEO Decision Engine"
echo "============================================================"

for file in \
  "$AGENTS/ceo_decision_engine.py" \
  "$CTL/decisionctl" \
  "$MEMORY/ceo_decision_config.json" \
  "$MEMORY/ceo_decision_queue.json" \
  "$MEMORY/ceo_decision_history.json" \
  "$MEMORY/ceo_decision_briefing.json" \
  "$MEMORY/ceo_decision_health.json" \
  "$MEMORY/ceo_decision_audit.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/ceo_decision_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_decision_preparation": true,
  "automatic_internal_explanations": true,
  "automatic_decision_approval": false,
  "automatic_task_execution": false,
  "automatic_customer_contact": false,
  "automatic_external_execution": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "owner_approval_required": true,
  "maximum_open_decisions": 20
}
JSON

[ -f "$MEMORY/ceo_decision_queue.json" ] || cat > "$MEMORY/ceo_decision_queue.json" <<'JSON'
{
  "schema_version": 1,
  "decisions": [],
  "statistics": {
    "total": 0,
    "pending": 0,
    "approved": 0,
    "deferred": 0,
    "rejected": 0
  },
  "last_updated_at": null
}
JSON

[ -f "$MEMORY/ceo_decision_history.json" ] || cat > "$MEMORY/ceo_decision_history.json" <<'JSON'
{
  "schema_version": 1,
  "history": [],
  "last_updated_at": null
}
JSON

cat > "$AGENTS/ceo_decision_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "ceo_decision_config.json"
QUEUE = MEMORY / "ceo_decision_queue.json"
HISTORY = MEMORY / "ceo_decision_history.json"
BRIEFING = MEMORY / "ceo_decision_briefing.json"
HEALTH = MEMORY / "ceo_decision_health.json"
AUDIT = MEMORY / "ceo_decision_audit.json"

PRIORITIES = MEMORY / "executive_priority_rankings.json"
EXECUTIVE = MEMORY / "ai_executive_briefing.json"
OPPORTUNITIES = MEMORY / "opportunity_discovery_results.json"


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


def make_id(seed: str) -> str:
    digest = hashlib.sha256(
        f"{seed}:{now()}".encode("utf-8")
    ).hexdigest()[:12]
    return f"decision-{digest}"


def number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


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


def update_stats(store: dict[str, Any]) -> None:
    records = store.get("decisions", [])
    statuses = ["pending", "approved", "deferred", "rejected"]

    stats = {"total": len(records)}
    for status in statuses:
        stats[status] = sum(
            1 for item in records
            if item.get("status") == status
        )

    store["statistics"] = stats
    store["last_updated_at"] = now()


def explain(priority: dict[str, Any]) -> dict[str, Any]:
    score = number(priority.get("score"), 0)
    value = number(priority.get("estimated_value"), 0)
    urgency = number(priority.get("urgency"), 0)
    risk = number(priority.get("risk_reduction"), 0)
    ease = number(priority.get("execution_ease"), 0)

    reasons = []

    if score >= 85:
        reasons.append("The overall priority score is critical.")
    elif score >= 70:
        reasons.append("The overall priority score is high.")
    else:
        reasons.append("The item is important but not immediately critical.")

    if value > 0:
        reasons.append(
            f"It has an estimated value of ${value:,.2f}."
        )

    if urgency >= 80:
        reasons.append("Delay may reduce revenue or increase operating risk.")

    if risk >= 80:
        reasons.append("Completing it would materially reduce business risk.")

    if ease >= 70:
        reasons.append("It appears practical to move forward internally.")

    tradeoffs = []
    if ease < 60:
        tradeoffs.append("Execution may require additional planning.")
    if value == 0:
        tradeoffs.append("Financial value is not yet quantified.")
    if priority.get("owner_approval_required"):
        tradeoffs.append("Owner approval is required before any external action.")

    return {
        "why_now": reasons,
        "tradeoffs": tradeoffs,
        "recommended_outcome": (
            "approve_internal_next_step"
            if not priority.get("owner_approval_required")
            else "owner_review_required"
        ),
    }


def prepare() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "ceo_decision_engine_disabled",
        }
        audit("prepare", result)
        return result

    priorities = load_json(
        PRIORITIES,
        {},
    ).get("rankings", {}).get("priorities", [])

    if not priorities:
        result = {
            "success": False,
            "status": "no_priorities_available",
        }
        audit("prepare", result)
        return result

    store = load_json(
        QUEUE,
        {
            "schema_version": 1,
            "decisions": [],
            "statistics": {},
        },
    )

    decisions = store.setdefault("decisions", [])
    existing_source_ids = {
        str(item.get("source_id"))
        for item in decisions
        if item.get("status") == "pending"
    }

    created = []

    maximum = int(config.get("maximum_open_decisions", 20))
    open_count = sum(
        1 for item in decisions
        if item.get("status") == "pending"
    )

    for priority in priorities:
        if open_count >= maximum:
            break

        source_id = str(priority.get("source_id"))

        if source_id in existing_source_ids:
            continue

        explanation = explain(priority)

        decision = {
            "id": make_id(source_id),
            "source_id": source_id,
            "source_type": priority.get("source_type"),
            "title": priority.get("title"),
            "category": priority.get("category"),
            "description": priority.get("description"),
            "rank": priority.get("rank"),
            "priority_score": priority.get("score"),
            "priority_band": priority.get("priority_band"),
            "estimated_value": number(
                priority.get("estimated_value"),
                0,
            ),
            "status": "pending",
            "recommended_action": priority.get(
                "recommended_action",
                "owner_review",
            ),
            "explanation": explanation,
            "owner_approval_required": True,
            "external_action_authorized": False,
            "automatic_execution": False,
            "created_at": now(),
            "updated_at": now(),
        }

        decisions.append(decision)
        created.append(decision)
        existing_source_ids.add(source_id)
        open_count += 1

    update_stats(store)
    save_json(QUEUE, store)

    top_pending = [
        item for item in decisions
        if item.get("status") == "pending"
    ]
    top_pending.sort(
        key=lambda item: (
            number(item.get("priority_score"), 0),
            number(item.get("estimated_value"), 0),
        ),
        reverse=True,
    )

    briefing = {
        "generated_at": now(),
        "headline": (
            f"{len(top_pending)} open CEO decision(s); "
            f"{len(created)} newly prepared."
        ),
        "top_decisions": top_pending[:5],
        "decision_counts": store.get("statistics", {}),
        "total_open_estimated_value": round(
            sum(
                number(item.get("estimated_value"), 0)
                for item in top_pending
            ),
            2,
        ),
        "automatic_decision_approval": False,
        "automatic_task_execution": False,
        "automatic_external_execution": False,
        "automatic_spending": False,
    }

    save_json(
        BRIEFING,
        {
            "schema_version": 1,
            "briefing": briefing,
            "last_updated_at": now(),
        },
    )

    save_json(
        HEALTH,
        {
            "healthy": True,
            "last_prepared_at": now(),
            "created_count": len(created),
            "open_decision_count": len(top_pending),
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "ceo_decisions_prepared",
        "created_count": len(created),
        "open_decision_count": len(top_pending),
        "briefing": briefing,
    }

    audit("prepare", result)
    return result


def decide(
    decision_id: str,
    outcome: str,
    reason: str | None = None,
) -> dict[str, Any]:
    allowed = {"approved", "deferred", "rejected"}

    if outcome not in allowed:
        result = {
            "success": False,
            "status": "invalid_decision_outcome",
            "allowed_outcomes": sorted(allowed),
        }
        audit("decide", result)
        return result

    store = load_json(QUEUE, {})

    decision = next(
        (
            item
            for item in store.get("decisions", [])
            if item.get("id") == decision_id
        ),
        None,
    )

    if not decision:
        result = {
            "success": False,
            "status": "decision_not_found",
            "decision_id": decision_id,
        }
        audit("decide", result)
        return result

    previous = decision.get("status")
    decision["status"] = outcome
    decision["owner_decision_reason"] = reason
    decision["decided_at"] = now()
    decision["updated_at"] = now()
    decision["external_action_authorized"] = False
    decision["automatic_execution"] = False

    update_stats(store)
    save_json(QUEUE, store)

    history = load_json(
        HISTORY,
        {
            "schema_version": 1,
            "history": [],
            "last_updated_at": None,
        },
    )

    history.setdefault("history", []).append({
        "decision_id": decision_id,
        "title": decision.get("title"),
        "previous_status": previous,
        "outcome": outcome,
        "reason": reason,
        "priority_score": decision.get("priority_score"),
        "estimated_value": decision.get("estimated_value"),
        "external_action_authorized": False,
        "automatic_execution": False,
        "decided_at": now(),
    })

    history["last_updated_at"] = now()
    save_json(HISTORY, history)

    result = {
        "success": True,
        "status": "ceo_decision_recorded",
        "decision_id": decision_id,
        "previous_status": previous,
        "outcome": outcome,
        "reason": reason,
        "external_action_authorized": False,
        "automatic_execution": False,
    }

    audit("decide", result)
    return result


def list_decisions() -> dict[str, Any]:
    store = load_json(QUEUE, {})

    result = {
        "success": True,
        "status": "ceo_decision_list",
        "statistics": store.get("statistics", {}),
        "decisions": store.get("decisions", []),
    }

    audit("list", result)
    return result


def pending() -> dict[str, Any]:
    records = [
        item for item in load_json(QUEUE, {}).get("decisions", [])
        if item.get("status") == "pending"
    ]

    records.sort(
        key=lambda item: number(item.get("priority_score"), 0),
        reverse=True,
    )

    result = {
        "success": True,
        "status": "pending_ceo_decisions",
        "count": len(records),
        "decisions": records,
    }

    audit("pending", result)
    return result


def history() -> dict[str, Any]:
    store = load_json(HISTORY, {})

    result = {
        "success": True,
        "status": "ceo_decision_history",
        "count": len(store.get("history", [])),
        "history": store.get("history", []),
    }

    audit("history", result)
    return result


def briefing() -> dict[str, Any]:
    data = load_json(BRIEFING, {}).get("briefing")

    result = {
        "success": bool(data),
        "status": "ceo_decision_briefing",
        "briefing": data,
    }

    audit("briefing", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    health = load_json(HEALTH, {})
    queue = load_json(QUEUE, {})

    result = {
        "success": True,
        "status": "ceo_decision_engine_status",
        "enabled": config.get("enabled", False),
        "automatic_internal_decision_preparation": config.get(
            "automatic_internal_decision_preparation", False
        ),
        "automatic_internal_explanations": config.get(
            "automatic_internal_explanations", False
        ),
        "automatic_decision_approval": config.get(
            "automatic_decision_approval", False
        ),
        "automatic_task_execution": config.get(
            "automatic_task_execution", False
        ),
        "automatic_customer_contact": config.get(
            "automatic_customer_contact", False
        ),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_publication": config.get(
            "automatic_publication", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "statistics": queue.get("statistics", {}),
        "health": health,
    }

    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "prepare":
            return print_result(prepare())

        if action == "approve":
            if len(sys.argv) < 3:
                raise ValueError("Decision ID is required")
            reason = " ".join(sys.argv[3:]).strip() or None
            return print_result(
                decide(sys.argv[2], "approved", reason)
            )

        if action == "defer":
            if len(sys.argv) < 3:
                raise ValueError("Decision ID is required")
            reason = " ".join(sys.argv[3:]).strip() or None
            return print_result(
                decide(sys.argv[2], "deferred", reason)
            )

        if action == "reject":
            if len(sys.argv) < 3:
                raise ValueError("Decision ID is required")
            reason = " ".join(sys.argv[3:]).strip() or None
            return print_result(
                decide(sys.argv[2], "rejected", reason)
            )

        if action == "list":
            return print_result(list_decisions())

        if action == "pending":
            return print_result(pending())

        if action == "history":
            return print_result(history())

        if action == "briefing":
            return print_result(briefing())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_decision_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "ceo_decision_error",
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
PY

chmod +x "$AGENTS/ceo_decision_engine.py"

cat > "$CTL/decisionctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "ceo_decision_engine.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/decisionctl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/ceo_decision_engine.py" \
  "$CTL/decisionctl"

echo "[2/5] Preparing CEO decisions..."
python "$CTL/decisionctl" prepare

echo "[3/5] Checking decision outputs..."
python "$CTL/decisionctl" pending
python "$CTL/decisionctl" briefing
python "$CTL/decisionctl" status

echo "[4/5] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "ceo_decision_engine.py",
    root / "companyos" / "decisionctl",
    root / "ceo_memory" / "ceo_decision_config.json",
    root / "ceo_memory" / "ceo_decision_queue.json",
    root / "ceo_memory" / "ceo_decision_briefing.json",
    root / "ceo_memory" / "ceo_decision_health.json",
]

for path in required:
    if not path.exists():
        errors.append(f"Missing: {path}")
    elif path.stat().st_size <= 0:
        errors.append(f"Empty: {path}")

for path in required[:2]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(f"Compile error: {exc}")

try:
    config = json.loads(required[2].read_text(encoding="utf-8"))

    for field in [
        "automatic_decision_approval",
        "automatic_task_execution",
        "automatic_customer_contact",
        "automatic_external_execution",
        "automatic_publication",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

except Exception as exc:
    errors.append(f"Config error: {exc}")

try:
    queue = json.loads(
        required[3].read_text(encoding="utf-8")
    ).get("decisions", [])

    if not queue:
        errors.append("No CEO decisions were prepared")

    for item in queue:
        if item.get("status") != "pending":
            errors.append("Decision was automatically decided")
            break

        if item.get("external_action_authorized") is not False:
            errors.append("External action was authorized automatically")
            break

        if item.get("automatic_execution") is not False:
            errors.append("Decision execution was enabled automatically")
            break

    briefing = json.loads(
        required[4].read_text(encoding="utf-8")
    ).get("briefing", {})

    for field in [
        "headline",
        "top_decisions",
        "decision_counts",
        "total_open_estimated_value",
    ]:
        if field not in briefing:
            errors.append(f"Briefing missing field: {field}")

except Exception as exc:
    errors.append(f"Decision data error: {exc}")

print("--------------------------------------------")
print("Phase 17 Step 4 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo "[5/5] Complete."

echo
echo "============================================================"
echo " PHASE 17 STEP 4 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/decisionctl prepare"
echo "  python companyos/decisionctl pending"
echo "  python companyos/decisionctl briefing"
echo "  python companyos/decisionctl approve DECISION_ID \"REASON\""
echo "  python companyos/decisionctl defer DECISION_ID \"REASON\""
echo "  python companyos/decisionctl reject DECISION_ID \"REASON\""
echo "  python companyos/decisionctl history"
echo "  python companyos/decisionctl status"
