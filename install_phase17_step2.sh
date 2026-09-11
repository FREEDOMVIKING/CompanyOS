#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase17_step2_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$BACKUP"

echo "============================================================"
echo " Phase 17 Step 2 - Opportunity Discovery Engine"
echo "============================================================"

for file in \
  "$AGENTS/opportunity_discovery_engine.py" \
  "$CTL/opportunitydiscoveryctl" \
  "$MEMORY/opportunity_discovery_config.json" \
  "$MEMORY/opportunity_discovery_results.json" \
  "$MEMORY/opportunity_discovery_health.json" \
  "$MEMORY/opportunity_discovery_audit.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/opportunity_discovery_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_internal_discovery": true,
  "automatic_internal_scoring": true,
  "automatic_external_research": false,
  "automatic_customer_contact": false,
  "automatic_campaign_launch": false,
  "automatic_external_execution": false,
  "automatic_publication": false,
  "automatic_spending": false,
  "owner_approval_required_for_external_actions": true,
  "minimum_score": 55,
  "maximum_results": 25
}
JSON

cat > "$AGENTS/opportunity_discovery_engine.py" <<'PY'
#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "opportunity_discovery_config.json"
RESULTS = MEMORY / "opportunity_discovery_results.json"
HEALTH = MEMORY / "opportunity_discovery_health.json"
AUDIT = MEMORY / "opportunity_discovery_audit.json"

LEADS = MEMORY / "crm_leads.json"
CUSTOMERS = MEMORY / "crm_customers.json"
QUOTES = MEMORY / "quote_registry.json"
PROJECTS = MEMORY / "project_registry.json"
INVOICES = MEMORY / "invoice_registry.json"
ACTIVITY = MEMORY / "business_activity_feed.json"


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


def make_id(seed: str) -> str:
    digest = hashlib.sha256(
        f"{seed}:{now()}".encode("utf-8")
    ).hexdigest()[:12]
    return f"oppdisc-{digest}"


def money(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except Exception:
        return 0.0


def score_opportunity(
    confidence: int,
    revenue_potential: int,
    ease: int,
    evidence: int,
) -> int:
    score = (
        confidence * 0.30
        + revenue_potential * 0.30
        + ease * 0.20
        + evidence * 0.20
    )
    return max(0, min(100, round(score)))


def build_opportunity(
    title: str,
    category: str,
    description: str,
    source: str,
    confidence: int,
    revenue_potential: int,
    ease: int,
    evidence: int,
    estimated_value: float = 0.0,
) -> dict[str, Any]:
    score = score_opportunity(
        confidence,
        revenue_potential,
        ease,
        evidence,
    )

    return {
        "id": make_id(f"{title}:{source}"),
        "title": title,
        "category": category,
        "description": description,
        "source": source,
        "score": score,
        "confidence": confidence,
        "revenue_potential": revenue_potential,
        "ease_of_execution": ease,
        "evidence_strength": evidence,
        "estimated_value": round(estimated_value, 2),
        "status": "discovered",
        "owner_approval_required": True,
        "external_action_authorized": False,
        "created_at": now(),
    }


def discover() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "opportunity_discovery_disabled",
        }
        audit("discover", result)
        return result

    leads = load_json(LEADS, {}).get("leads", [])
    customers = load_json(CUSTOMERS, {}).get("customers", [])
    quotes = load_json(QUOTES, {}).get("quotes", [])
    projects = load_json(PROJECTS, {}).get("projects", [])
    invoices = load_json(INVOICES, {}).get("invoices", [])
    activity = load_json(ACTIVITY, {}).get("activities", [])

    opportunities: list[dict[str, Any]] = []

    open_leads = [
        x for x in leads
        if x.get("status") in {"new", "contacted", "qualified", "hold"}
    ]

    for lead in open_leads:
        amount = money(lead.get("estimate_amount"))
        opportunities.append(
            build_opportunity(
                title=f"Advance lead: {lead.get('project_name')}",
                category="sales",
                description=(
                    f"Move {lead.get('customer_name')} from "
                    f"{lead.get('status')} toward an approved proposal."
                ),
                source=str(lead.get("id")),
                confidence=78,
                revenue_potential=85 if amount > 0 else 65,
                ease=72,
                evidence=82,
                estimated_value=amount,
            )
        )

    dormant_leads = [
        x for x in leads
        if x.get("status") in {"lost", "hold"}
    ]

    for lead in dormant_leads:
        opportunities.append(
            build_opportunity(
                title=f"Re-engage dormant lead: {lead.get('customer_name')}",
                category="reactivation",
                description=(
                    f"Review whether {lead.get('project_name')} can be "
                    "reopened with a revised scope or timing."
                ),
                source=str(lead.get("id")),
                confidence=58,
                revenue_potential=68,
                ease=70,
                evidence=62,
                estimated_value=money(lead.get("estimate_amount")),
            )
        )

    completed_projects = [
        x for x in projects
        if x.get("status") == "completed"
    ]

    for project in completed_projects:
        opportunities.append(
            build_opportunity(
                title=f"Upsell completed customer: {project.get('customer_name')}",
                category="upsell",
                description=(
                    f"Review adjacent services related to "
                    f"{project.get('project_name')}."
                ),
                source=str(project.get("id")),
                confidence=72,
                revenue_potential=74,
                ease=76,
                evidence=78,
                estimated_value=money(project.get("amount")) * 0.25,
            )
        )

    project_names = [
        str(x.get("project_name") or "").strip()
        for x in projects
        if str(x.get("project_name") or "").strip()
    ]

    common_projects = Counter(project_names)

    for project_name, count in common_projects.items():
        if count < 2:
            continue

        related = [
            x for x in projects
            if x.get("project_name") == project_name
        ]

        average_value = (
            sum(money(x.get("amount")) for x in related) / len(related)
            if related
            else 0
        )

        opportunities.append(
            build_opportunity(
                title=f"Productize repeat service: {project_name}",
                category="productization",
                description=(
                    f"{project_name} has appeared {count} times and may "
                    "support a repeatable package, template, or fixed-price offer."
                ),
                source=f"project_pattern:{project_name}",
                confidence=82,
                revenue_potential=88,
                ease=64,
                evidence=85,
                estimated_value=average_value,
            )
        )

    unpaid_invoices = [
        x for x in invoices
        if money(x.get("balance_due")) > 0
        and x.get("status") != "void"
    ]

    for invoice in unpaid_invoices:
        opportunities.append(
            build_opportunity(
                title=f"Recover receivable: {invoice.get('customer_name')}",
                category="cash_recovery",
                description=(
                    f"Internally review invoice {invoice.get('id')} with "
                    f"${money(invoice.get('balance_due')):,.2f} outstanding."
                ),
                source=str(invoice.get("id")),
                confidence=92,
                revenue_potential=90,
                ease=68,
                evidence=95,
                estimated_value=money(invoice.get("balance_due")),
            )
        )

    if customers and not completed_projects:
        opportunities.append(
            build_opportunity(
                title="Create first customer retention offer",
                category="retention",
                description=(
                    "Use existing customer records to design a repeat-service "
                    "or maintenance offer for owner review."
                ),
                source="customer_base",
                confidence=64,
                revenue_potential=70,
                ease=66,
                evidence=58,
                estimated_value=0,
            )
        )

    if len(activity) >= 5:
        opportunities.append(
            build_opportunity(
                title="Package internal operating workflow",
                category="digital_product",
                description=(
                    "The system has enough recurring activity to consider "
                    "turning an internal workflow into a reusable template."
                ),
                source="business_activity_feed",
                confidence=66,
                revenue_potential=72,
                ease=60,
                evidence=65,
                estimated_value=0,
            )
        )

    minimum_score = int(config.get("minimum_score", 55))
    maximum_results = int(config.get("maximum_results", 25))

    opportunities = [
        item for item in opportunities
        if int(item.get("score", 0)) >= minimum_score
    ]

    opportunities.sort(
        key=lambda item: (
            int(item.get("score", 0)),
            money(item.get("estimated_value")),
        ),
        reverse=True,
    )

    opportunities = opportunities[:maximum_results]

    total_estimated_value = round(
        sum(money(item.get("estimated_value")) for item in opportunities),
        2,
    )

    payload = {
        "generated_at": now(),
        "count": len(opportunities),
        "total_estimated_value": total_estimated_value,
        "opportunities": opportunities,
        "automatic_external_research": False,
        "automatic_customer_contact": False,
        "automatic_campaign_launch": False,
        "automatic_external_execution": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    save_json(
        RESULTS,
        {
            "schema_version": 1,
            "results": payload,
            "last_updated_at": now(),
        },
    )

    save_json(
        HEALTH,
        {
            "healthy": True,
            "last_generated_at": now(),
            "opportunity_count": len(opportunities),
            "total_estimated_value": total_estimated_value,
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "opportunity_discovery_complete",
        "results": payload,
    }

    audit("discover", result)
    return result


def show() -> dict[str, Any]:
    results = load_json(RESULTS, {}).get("results")

    result = {
        "success": bool(results),
        "status": "opportunity_discovery_results",
        "results": results,
    }

    audit("show", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "opportunity_discovery_status",
        "enabled": config.get("enabled", False),
        "automatic_internal_discovery": config.get(
            "automatic_internal_discovery", False
        ),
        "automatic_internal_scoring": config.get(
            "automatic_internal_scoring", False
        ),
        "automatic_external_research": config.get(
            "automatic_external_research", False
        ),
        "automatic_customer_contact": config.get(
            "automatic_customer_contact", False
        ),
        "automatic_campaign_launch": config.get(
            "automatic_campaign_launch", False
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
        if action == "discover":
            return print_result(discover())

        if action == "show":
            return print_result(show())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_opportunity_discovery_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "opportunity_discovery_error",
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

chmod +x "$AGENTS/opportunity_discovery_engine.py"

cat > "$CTL/opportunitydiscoveryctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "opportunity_discovery_engine.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/opportunitydiscoveryctl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/opportunity_discovery_engine.py" \
  "$CTL/opportunitydiscoveryctl"

echo "[2/5] Running opportunity discovery..."
python "$CTL/opportunitydiscoveryctl" discover

echo "[3/5] Checking discovery engine..."
python "$CTL/opportunitydiscoveryctl" show
python "$CTL/opportunitydiscoveryctl" status

echo "[4/5] Verifying..."
python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "opportunity_discovery_engine.py",
    root / "companyos" / "opportunitydiscoveryctl",
    root / "ceo_memory" / "opportunity_discovery_config.json",
    root / "ceo_memory" / "opportunity_discovery_results.json",
    root / "ceo_memory" / "opportunity_discovery_health.json",
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
        "automatic_external_research",
        "automatic_customer_contact",
        "automatic_campaign_launch",
        "automatic_external_execution",
        "automatic_publication",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

except Exception as exc:
    errors.append(f"Config error: {exc}")

try:
    results = json.loads(
        required[3].read_text(encoding="utf-8")
    ).get("results", {})

    for field in [
        "count",
        "total_estimated_value",
        "opportunities",
    ]:
        if field not in results:
            errors.append(f"Results missing field: {field}")

    opportunities = results.get("opportunities", [])

    if not opportunities:
        errors.append("No opportunities were discovered")

    for item in opportunities:
        if item.get("external_action_authorized") is not False:
            errors.append("External action was authorized automatically")
            break

except Exception as exc:
    errors.append(f"Results error: {exc}")

print("--------------------------------------------")
print("Phase 17 Step 2 verification")
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
echo " PHASE 17 STEP 2 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/opportunitydiscoveryctl discover"
echo "  python companyos/opportunitydiscoveryctl show"
echo "  python companyos/opportunitydiscoveryctl status"
