#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase17_step1_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$BACKUP"

echo "============================================================"
echo " Phase 17 Step 1 - AI Executive Assistant"
echo "============================================================"

for file in \
  "$AGENTS/ai_executive_assistant.py" \
  "$CTL/executivectl" \
  "$MEMORY/ai_executive_config.json" \
  "$MEMORY/ai_executive_briefing.json" \
  "$MEMORY/ai_executive_health.json" \
  "$MEMORY/ai_executive_audit.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/ai_executive_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_analysis": true,
  "automatic_internal_planning": true,
  "automatic_external_execution": false,
  "automatic_customer_contact": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "owner_approval_required_for_external_actions": true,
  "max_recommendations": 10
}
JSON

cat > "$AGENTS/ai_executive_assistant.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "ai_executive_config.json"
BRIEFING = MEMORY / "ai_executive_briefing.json"
HEALTH = MEMORY / "ai_executive_health.json"
AUDIT = MEMORY / "ai_executive_audit.json"

BI = MEMORY / "business_intelligence_snapshot.json"
CRM = MEMORY / "crm_leads.json"
QUOTES = MEMORY / "quote_registry.json"
PROJECTS = MEMORY / "project_registry.json"
FOLLOWUPS = MEMORY / "sales_followups.json"
INVOICES = MEMORY / "invoice_registry.json"
PAYMENTS = MEMORY / "payment_registry.json"
EXPENSES = MEMORY / "expense_registry.json"
TASKS = MEMORY / "product_execution_tasks.json"


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


def money(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except Exception:
        return 0.0


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


def build_recommendations(
    leads: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    followups: list[dict[str, Any]],
    invoices: list[dict[str, Any]],
    tasks: list[dict[str, Any]],
    net_cash: float,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []

    new_leads = [x for x in leads if x.get("status") == "new"]
    pending_followups = [x for x in followups if x.get("status") == "pending"]
    open_invoices = [
        x for x in invoices
        if money(x.get("balance_due")) > 0
        and x.get("status") != "void"
    ]
    stalled_projects = [
        x for x in projects
        if x.get("status") in {"planning", "waiting"}
        and int(x.get("progress_percent") or 0) < 25
    ]
    pending_tasks = [x for x in tasks if x.get("status") == "pending"]

    if new_leads:
        recs.append({
            "priority": 1,
            "category": "sales",
            "action": "Review and qualify new leads",
            "reason": f"{len(new_leads)} new lead(s) are waiting.",
            "external_action_required": False,
        })

    if pending_followups:
        recs.append({
            "priority": 1,
            "category": "sales",
            "action": "Review pending follow-ups",
            "reason": f"{len(pending_followups)} follow-up(s) are pending.",
            "external_action_required": False,
        })

    if open_invoices:
        recs.append({
            "priority": 1,
            "category": "finance",
            "action": "Review outstanding receivables",
            "reason": f"{len(open_invoices)} invoice(s) have unpaid balances.",
            "external_action_required": False,
        })

    if net_cash < 0:
        recs.append({
            "priority": 1,
            "category": "finance",
            "action": "Reduce cash burn",
            "reason": "Recorded expenses exceed recorded payments.",
            "external_action_required": False,
        })

    if stalled_projects:
        recs.append({
            "priority": 2,
            "category": "operations",
            "action": "Review stalled projects",
            "reason": f"{len(stalled_projects)} project(s) show low progress.",
            "external_action_required": False,
        })

    if pending_tasks:
        recs.append({
            "priority": 2,
            "category": "operations",
            "action": "Work the internal task queue",
            "reason": f"{len(pending_tasks)} internal task(s) are pending.",
            "external_action_required": False,
        })

    if not recs:
        recs.append({
            "priority": 3,
            "category": "general",
            "action": "Maintain current operating rhythm",
            "reason": "No major internal issues detected.",
            "external_action_required": False,
        })

    return sorted(recs, key=lambda x: x["priority"])


def generate() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "ai_executive_disabled",
        }
        audit("generate", result)
        return result

    bi = load_json(BI, {}).get("snapshot", {})
    leads = load_json(CRM, {}).get("leads", [])
    quotes = load_json(QUOTES, {}).get("quotes", [])
    projects = load_json(PROJECTS, {}).get("projects", [])
    followups = load_json(FOLLOWUPS, {}).get("followups", [])
    invoices = load_json(INVOICES, {}).get("invoices", [])
    payments = load_json(PAYMENTS, {}).get("payments", [])
    expenses = load_json(EXPENSES, {}).get("expenses", [])
    tasks = load_json(TASKS, {}).get("tasks", [])

    cash_received = sum(money(x.get("amount")) for x in payments)
    expense_total = sum(money(x.get("amount")) for x in expenses)
    net_cash = round(cash_received - expense_total, 2)

    pipeline_value = sum(
        money(x.get("estimate_amount"))
        for x in leads
        if x.get("status") not in {"won", "lost"}
    )

    receivables = sum(
        money(x.get("balance_due"))
        for x in invoices
    )

    recommendations = build_recommendations(
        leads,
        projects,
        followups,
        invoices,
        tasks,
        net_cash,
    )[: int(config.get("max_recommendations", 10))]

    risk_flags = []
    if net_cash < 0:
        risk_flags.append("negative_cash_position")
    if receivables > 0:
        risk_flags.append("open_receivables")
    if any(x.get("status") == "new" for x in leads):
        risk_flags.append("unqualified_leads")
    if any(x.get("status") == "pending" for x in followups):
        risk_flags.append("pending_followups")
    if any(
        x.get("status") in {"planning", "waiting"}
        and int(x.get("progress_percent") or 0) < 25
        for x in projects
    ):
        risk_flags.append("stalled_projects")

    opportunity_flags = []
    if pipeline_value > 0:
        opportunity_flags.append("active_sales_pipeline")
    if quotes:
        opportunity_flags.append("quote_inventory_available")
    if projects:
        opportunity_flags.append("active_delivery_capacity")
    if receivables > 0:
        opportunity_flags.append("cash_collection_opportunity")

    briefing = {
        "generated_at": now(),
        "company_health": bi.get("company_health", "unknown"),
        "company_score": bi.get("company_score", 0),
        "executive_summary": {
            "lead_count": len(leads),
            "quote_count": len(quotes),
            "project_count": len(projects),
            "pending_followups": sum(
                1 for x in followups
                if x.get("status") == "pending"
            ),
            "pending_internal_tasks": sum(
                1 for x in tasks
                if x.get("status") == "pending"
            ),
            "pipeline_value": round(pipeline_value, 2),
            "accounts_receivable": round(receivables, 2),
            "net_cash_position": net_cash,
        },
        "risk_flags": risk_flags,
        "opportunity_flags": opportunity_flags,
        "recommended_next_actions": recommendations,
        "internal_plan": [
            {
                "order": index + 1,
                "action": item["action"],
                "category": item["category"],
                "owner_approval_required": False,
                "external_execution": False,
            }
            for index, item in enumerate(recommendations)
        ],
        "automatic_external_execution": False,
        "automatic_customer_contact": False,
        "automatic_publication": False,
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
            "last_generated_at": now(),
            "recommendation_count": len(recommendations),
            "risk_count": len(risk_flags),
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "ai_executive_briefing_generated",
        "briefing": briefing,
    }

    audit("generate", result)
    return result


def show() -> dict[str, Any]:
    briefing = load_json(BRIEFING, {}).get("briefing")

    result = {
        "success": bool(briefing),
        "status": "ai_executive_briefing",
        "briefing": briefing,
    }

    audit("show", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "ai_executive_status",
        "enabled": config.get("enabled", False),
        "automatic_internal_analysis": config.get(
            "automatic_internal_analysis", False
        ),
        "automatic_internal_planning": config.get(
            "automatic_internal_planning", False
        ),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_customer_contact": config.get(
            "automatic_customer_contact", False
        ),
        "automatic_publication": config.get(
            "automatic_publication", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
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
        if action == "generate":
            return print_result(generate())

        if action == "show":
            return print_result(show())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_executive_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "ai_executive_error",
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

chmod +x "$AGENTS/ai_executive_assistant.py"

cat > "$CTL/executivectl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "ai_executive_assistant.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/executivectl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/ai_executive_assistant.py" \
  "$CTL/executivectl"

echo "[2/5] Generating executive briefing..."
python "$CTL/executivectl" generate

echo "[3/5] Checking executive assistant..."
python "$CTL/executivectl" show
python "$CTL/executivectl" status

echo "[4/5] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "ai_executive_assistant.py",
    root / "companyos" / "executivectl",
    root / "ceo_memory" / "ai_executive_config.json",
    root / "ceo_memory" / "ai_executive_briefing.json",
    root / "ceo_memory" / "ai_executive_health.json",
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
        "automatic_external_execution",
        "automatic_customer_contact",
        "automatic_publication",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

except Exception as exc:
    errors.append(f"Config error: {exc}")

try:
    briefing = json.loads(
        required[3].read_text(encoding="utf-8")
    ).get("briefing", {})

    for field in [
        "executive_summary",
        "risk_flags",
        "opportunity_flags",
        "recommended_next_actions",
        "internal_plan",
    ]:
        if field not in briefing:
            errors.append(f"Briefing missing field: {field}")

    if not briefing.get("recommended_next_actions"):
        errors.append("No executive recommendations generated")

except Exception as exc:
    errors.append(f"Briefing error: {exc}")

print("--------------------------------------------")
print("Phase 17 Step 1 verification")
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
echo " PHASE 17 STEP 1 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/executivectl generate"
echo "  python companyos/executivectl show"
echo "  python companyos/executivectl status"
