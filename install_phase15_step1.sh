#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
COMPANYOS="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
BACKUP="$ROOT/backups/phase15_step1_$(date +%Y%m%d_%H%M%S)"

echo "============================================================"
echo " Phase 15 Step 1 - Opportunity Discovery Scanner"
echo "============================================================"

cd "$ROOT"

mkdir -p "$AGENTS" "$COMPANYOS" "$MEMORY" "$BACKUP"

echo "[1/9] Creating backups..."

for file in \
    "$AGENTS/opportunity_scanner.py" \
    "$COMPANYOS/opportunityctl" \
    "$MEMORY/opportunity_scanner_config.json" \
    "$MEMORY/discovered_opportunities.json" \
    "$MEMORY/opportunity_scanner_health.json"
do
    if [ -f "$file" ]; then
        cp -a "$file" "$BACKUP/"
    fi
done

echo "[2/9] Creating scanner configuration..."

cat > "$MEMORY/opportunity_scanner_config.json" <<'JSON'
{
  "enabled": true,
  "scanner_mode": "internal",
  "automatic_scanning": false,
  "automatic_project_creation": false,
  "automatic_external_research": false,
  "automatic_spending": false,
  "automatic_publication": false,
  "maximum_new_opportunities_per_scan": 12,
  "minimum_discovery_score": 35,
  "allowed_categories": [
    "ai_automation",
    "small_business_tools",
    "developer_tools",
    "digital_products",
    "operations",
    "local_services"
  ],
  "discovery_sources": [
    "company_capabilities",
    "portfolio_gaps",
    "product_factory_patterns",
    "operational_problems",
    "revenue_model_templates"
  ]
}
JSON

echo "[3/9] Creating opportunity memory..."

if [ ! -f "$MEMORY/discovered_opportunities.json" ]; then
cat > "$MEMORY/discovered_opportunities.json" <<'JSON'
{
  "schema_version": 1,
  "opportunities": [],
  "statistics": {
    "total_discovered": 0,
    "active": 0,
    "archived": 0,
    "converted_to_proposal": 0
  },
  "last_scan_at": null
}
JSON
fi

echo "[4/9] Creating Opportunity Scanner agent..."

cat > "$AGENTS/opportunity_scanner.py" <<'PY'
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

CONFIG_PATH = MEMORY / "opportunity_scanner_config.json"
OPPORTUNITIES_PATH = MEMORY / "discovered_opportunities.json"
HEALTH_PATH = MEMORY / "opportunity_scanner_health.json"
AUDIT_PATH = MEMORY / "opportunity_scanner_audit.json"


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


def opportunity_id(title: str) -> str:
    digest = hashlib.sha256(title.lower().encode("utf-8")).hexdigest()[:12]
    return f"opp-{digest}"


def read_existing_project_names() -> list[str]:
    names: list[str] = []

    possible_files = [
        MEMORY / "portfolio.json",
        MEMORY / "portfolio_state.json",
        MEMORY / "products.json",
        MEMORY / "product_factory.json",
        MEMORY / "project_registry.json",
    ]

    for path in possible_files:
        data = load_json(path, {})

        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = []

            for key in (
                "projects",
                "products",
                "portfolio",
                "items",
                "businesses",
            ):
                value = data.get(key)

                if isinstance(value, list):
                    records.extend(value)
        else:
            records = []

        for record in records:
            if isinstance(record, str):
                names.append(record)
            elif isinstance(record, dict):
                name = (
                    record.get("name")
                    or record.get("title")
                    or record.get("project_name")
                    or record.get("product_name")
                )

                if name:
                    names.append(str(name))

    return sorted(set(names))


def candidate_templates() -> list[dict[str, Any]]:
    return [
        {
            "title": "AI Quote and Estimate Assistant",
            "category": "small_business_tools",
            "problem": (
                "Small service businesses lose time preparing estimates "
                "and following up with potential customers."
            ),
            "solution": (
                "A mobile-friendly assistant that turns job details into "
                "professional estimates, follow-up messages and work scopes."
            ),
            "target_customer": (
                "Contractors, landscapers, cleaners and local service companies"
            ),
            "revenue_model": "Monthly subscription",
            "estimated_build_effort": 42,
            "estimated_market_demand": 78,
            "estimated_revenue_potential": 76,
            "strategic_fit": 92,
        },
        {
            "title": "Local Business Review Response Agent",
            "category": "ai_automation",
            "problem": (
                "Local businesses often fail to respond consistently to "
                "customer reviews."
            ),
            "solution": (
                "An approval-based AI assistant that drafts personalized "
                "review responses and tracks unresolved complaints."
            ),
            "target_customer": "Local restaurants, shops and service companies",
            "revenue_model": "Subscription plus setup fee",
            "estimated_build_effort": 35,
            "estimated_market_demand": 72,
            "estimated_revenue_potential": 68,
            "strategic_fit": 88,
        },
        {
            "title": "Mobile Jobsite Daily Report Generator",
            "category": "operations",
            "problem": (
                "Construction crews frequently produce incomplete or "
                "inconsistent daily job reports."
            ),
            "solution": (
                "A phone-based reporting tool that converts notes, quantities "
                "and photos into structured daily reports."
            ),
            "target_customer": "Small and medium construction contractors",
            "revenue_model": "Per-company subscription",
            "estimated_build_effort": 48,
            "estimated_market_demand": 75,
            "estimated_revenue_potential": 74,
            "strategic_fit": 95,
        },
        {
            "title": "Small Business Document Pack Builder",
            "category": "digital_products",
            "problem": (
                "New small businesses need basic forms, policies and operating "
                "documents but do not know where to begin."
            ),
            "solution": (
                "A guided generator for estimates, invoices, intake forms, "
                "checklists and standard operating procedures."
            ),
            "target_customer": "New service businesses and solo operators",
            "revenue_model": "One-time purchase with premium templates",
            "estimated_build_effort": 30,
            "estimated_market_demand": 70,
            "estimated_revenue_potential": 65,
            "strategic_fit": 90,
        },
        {
            "title": "AI Lead Qualification Inbox",
            "category": "ai_automation",
            "problem": (
                "Small companies waste time manually sorting low-quality "
                "inquiries from serious buyers."
            ),
            "solution": (
                "A lead inbox that scores inquiries, drafts replies and "
                "identifies the next best action."
            ),
            "target_customer": "Local service companies and independent sales teams",
            "revenue_model": "Monthly subscription",
            "estimated_build_effort": 55,
            "estimated_market_demand": 80,
            "estimated_revenue_potential": 82,
            "strategic_fit": 84,
        },
        {
            "title": "Repository Health and Release Assistant",
            "category": "developer_tools",
            "problem": (
                "Small development teams struggle to maintain release notes, "
                "checks and repository hygiene."
            ),
            "solution": (
                "A GitHub-connected assistant that reviews repository health, "
                "creates release checklists and drafts changelogs."
            ),
            "target_customer": "Solo developers and small software teams",
            "revenue_model": "Subscription",
            "estimated_build_effort": 58,
            "estimated_market_demand": 66,
            "estimated_revenue_potential": 71,
            "strategic_fit": 94,
        },
        {
            "title": "Service Business Follow-Up Scheduler",
            "category": "small_business_tools",
            "problem": (
                "Potential customers are lost when estimates and inquiries "
                "are not followed up consistently."
            ),
            "solution": (
                "A lightweight system that schedules reminders and drafts "
                "customer follow-up messages."
            ),
            "target_customer": "Contractors and appointment-based businesses",
            "revenue_model": "Low-cost monthly subscription",
            "estimated_build_effort": 32,
            "estimated_market_demand": 77,
            "estimated_revenue_potential": 69,
            "strategic_fit": 91,
        },
        {
            "title": "Operations Checklist Marketplace",
            "category": "digital_products",
            "problem": (
                "Small companies repeatedly rebuild the same operational "
                "checklists and training documents."
            ),
            "solution": (
                "A searchable marketplace of customizable checklists, SOPs "
                "and inspection templates."
            ),
            "target_customer": "Small companies across service industries",
            "revenue_model": "Template sales and creator revenue share",
            "estimated_build_effort": 50,
            "estimated_market_demand": 64,
            "estimated_revenue_potential": 72,
            "strategic_fit": 86,
        },
        {
            "title": "Local Contractor Bid Organizer",
            "category": "local_services",
            "problem": (
                "Small contractors often track bids, customer notes and job "
                "status through scattered messages and paper."
            ),
            "solution": (
                "A simple mobile dashboard for leads, estimates, bid status "
                "and customer follow-up."
            ),
            "target_customer": "Residential and light-commercial contractors",
            "revenue_model": "Monthly subscription",
            "estimated_build_effort": 44,
            "estimated_market_demand": 79,
            "estimated_revenue_potential": 73,
            "strategic_fit": 96,
        },
        {
            "title": "AI Product Validation Worksheet",
            "category": "digital_products",
            "problem": (
                "New founders build products before clearly testing demand, "
                "pricing and customer pain."
            ),
            "solution": (
                "A guided validation product that produces interview plans, "
                "risk scores and go-or-stop recommendations."
            ),
            "target_customer": "Solo founders and first-time entrepreneurs",
            "revenue_model": "One-time product plus premium reports",
            "estimated_build_effort": 25,
            "estimated_market_demand": 67,
            "estimated_revenue_potential": 62,
            "strategic_fit": 89,
        },
        {
            "title": "Automated Client Onboarding Portal",
            "category": "operations",
            "problem": (
                "Small companies manually collect the same customer details, "
                "documents and approvals for each new client."
            ),
            "solution": (
                "A customizable onboarding portal with forms, checklists, "
                "document requests and progress tracking."
            ),
            "target_customer": "Consultants, agencies and service businesses",
            "revenue_model": "Subscription",
            "estimated_build_effort": 63,
            "estimated_market_demand": 76,
            "estimated_revenue_potential": 84,
            "strategic_fit": 82,
        },
        {
            "title": "CompanyOS Starter Deployment Service",
            "category": "ai_automation",
            "problem": (
                "Individuals want private AI automation systems but struggle "
                "with installation, configuration and maintenance."
            ),
            "solution": (
                "A guided deployment package for private, approval-controlled "
                "AI business automation."
            ),
            "target_customer": "Technical entrepreneurs and small businesses",
            "revenue_model": "Setup fee plus support plan",
            "estimated_build_effort": 46,
            "estimated_market_demand": 69,
            "estimated_revenue_potential": 80,
            "strategic_fit": 98,
        },
    ]


def calculate_score(candidate: dict[str, Any]) -> int:
    demand = int(candidate.get("estimated_market_demand", 0))
    revenue = int(candidate.get("estimated_revenue_potential", 0))
    fit = int(candidate.get("strategic_fit", 0))
    effort = int(candidate.get("estimated_build_effort", 100))

    ease_score = max(0, 100 - effort)

    score = (
        demand * 0.30
        + revenue * 0.30
        + fit * 0.25
        + ease_score * 0.15
    )

    return round(score)


def scan() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "opportunity_scanner_disabled",
        }
        audit("scan", result)
        return result

    store = load_json(
        OPPORTUNITIES_PATH,
        {
            "schema_version": 1,
            "opportunities": [],
            "statistics": {},
            "last_scan_at": None,
        },
    )

    opportunities = store.setdefault("opportunities", [])
    existing_ids = {
        item.get("id")
        for item in opportunities
        if isinstance(item, dict)
    }

    existing_projects = {
        name.lower()
        for name in read_existing_project_names()
    }

    allowed_categories = set(config.get("allowed_categories", []))
    minimum_score = int(config.get("minimum_discovery_score", 35))
    maximum_new = int(
        config.get("maximum_new_opportunities_per_scan", 12)
    )

    added: list[dict[str, Any]] = []
    skipped_duplicates = 0
    skipped_low_score = 0

    candidates = candidate_templates()

    for candidate in candidates:
        if len(added) >= maximum_new:
            break

        if (
            allowed_categories
            and candidate.get("category") not in allowed_categories
        ):
            continue

        item_id = opportunity_id(candidate["title"])
        score = calculate_score(candidate)

        if (
            item_id in existing_ids
            or candidate["title"].lower() in existing_projects
        ):
            skipped_duplicates += 1
            continue

        if score < minimum_score:
            skipped_low_score += 1
            continue

        opportunity = {
            "id": item_id,
            "title": candidate["title"],
            "category": candidate["category"],
            "problem": candidate["problem"],
            "solution": candidate["solution"],
            "target_customer": candidate["target_customer"],
            "revenue_model": candidate["revenue_model"],
            "discovery_score": score,
            "estimated_market_demand": (
                candidate["estimated_market_demand"]
            ),
            "estimated_revenue_potential": (
                candidate["estimated_revenue_potential"]
            ),
            "estimated_build_effort": (
                candidate["estimated_build_effort"]
            ),
            "strategic_fit": candidate["strategic_fit"],
            "status": "discovered",
            "proposal_status": "not_created",
            "source": "internal_opportunity_scanner",
            "external_research_completed": False,
            "owner_approval_required": True,
            "created_at": now(),
            "updated_at": now(),
        }

        opportunities.append(opportunity)
        existing_ids.add(item_id)
        added.append(opportunity)

    opportunities.sort(
        key=lambda item: int(item.get("discovery_score", 0)),
        reverse=True,
    )

    active = sum(
        1
        for item in opportunities
        if item.get("status") not in {"archived", "rejected"}
    )

    archived = sum(
        1
        for item in opportunities
        if item.get("status") == "archived"
    )

    converted = sum(
        1
        for item in opportunities
        if item.get("proposal_status") == "created"
    )

    store["statistics"] = {
        "total_discovered": len(opportunities),
        "active": active,
        "archived": archived,
        "converted_to_proposal": converted,
    }
    store["last_scan_at"] = now()

    save_json(OPPORTUNITIES_PATH, store)

    health = {
        "healthy": True,
        "last_scan_at": store["last_scan_at"],
        "last_error": None,
        "total_opportunities": len(opportunities),
        "new_opportunities": len(added),
    }
    save_json(HEALTH_PATH, health)

    result = {
        "success": True,
        "status": "opportunity_scan_complete",
        "scanner_mode": config.get("scanner_mode", "internal"),
        "new_opportunities": len(added),
        "total_opportunities": len(opportunities),
        "skipped_duplicates": skipped_duplicates,
        "skipped_low_score": skipped_low_score,
        "automatic_project_creation": False,
        "automatic_external_research": False,
        "automatic_spending": False,
        "automatic_publication": False,
        "top_new_opportunities": [
            {
                "id": item["id"],
                "title": item["title"],
                "score": item["discovery_score"],
                "category": item["category"],
            }
            for item in added[:5]
        ],
    }

    audit("scan", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})
    store = load_json(OPPORTUNITIES_PATH, {})
    health = load_json(HEALTH_PATH, {})

    opportunities = store.get("opportunities", [])

    result = {
        "success": True,
        "status": "opportunity_scanner_status",
        "enabled": config.get("enabled", False),
        "scanner_mode": config.get("scanner_mode", "unknown"),
        "healthy": health.get("healthy", False),
        "last_scan_at": store.get("last_scan_at"),
        "statistics": store.get("statistics", {}),
        "automatic_scanning": config.get(
            "automatic_scanning",
            False,
        ),
        "automatic_project_creation": config.get(
            "automatic_project_creation",
            False,
        ),
        "automatic_external_research": config.get(
            "automatic_external_research",
            False,
        ),
        "top_opportunities": [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "score": item.get("discovery_score"),
                "status": item.get("status"),
            }
            for item in opportunities[:5]
        ],
    }

    audit("status", result)
    return result


def list_opportunities(limit: int = 20) -> dict[str, Any]:
    store = load_json(OPPORTUNITIES_PATH, {})
    opportunities = store.get("opportunities", [])

    limit = max(1, min(limit, 100))

    result = {
        "success": True,
        "status": "opportunity_list",
        "count": min(limit, len(opportunities)),
        "total": len(opportunities),
        "opportunities": [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "category": item.get("category"),
                "score": item.get("discovery_score"),
                "revenue_model": item.get("revenue_model"),
                "status": item.get("status"),
            }
            for item in opportunities[:limit]
        ],
    }

    audit("list", result)
    return result


def show_opportunity(item_id: str) -> dict[str, Any]:
    store = load_json(OPPORTUNITIES_PATH, {})

    for opportunity in store.get("opportunities", []):
        if opportunity.get("id") == item_id:
            result = {
                "success": True,
                "status": "opportunity_details",
                "opportunity": opportunity,
            }
            audit("show", result)
            return result

    result = {
        "success": False,
        "status": "opportunity_not_found",
        "id": item_id,
    }
    audit("show", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: opportunity_scanner.py "
            "scan|status|list [limit]|show <id>"
        )
        return 2

    action = sys.argv[1].lower()

    try:
        if action == "scan":
            return print_result(scan())

        if action == "status":
            return print_result(status())

        if action == "list":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            return print_result(list_opportunities(limit))

        if action == "show":
            if len(sys.argv) < 3:
                raise ValueError("Opportunity ID is required")
            return print_result(show_opportunity(sys.argv[2]))

        return print_result({
            "success": False,
            "status": "unknown_opportunity_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "opportunity_scanner_error",
            "action": action,
            "error": str(exc),
        }

        health = {
            "healthy": False,
            "last_checked_at": now(),
            "last_error": str(exc),
        }
        save_json(HEALTH_PATH, health)
        audit("error", result)

        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$AGENTS/opportunity_scanner.py"

echo "[5/9] Creating opportunity control command..."

cat > "$COMPANYOS/opportunityctl" <<'PY'
#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys


ROOT = Path.home() / "companyos"
SCANNER = ROOT / "agents" / "opportunity_scanner.py"


def main() -> int:
    if not SCANNER.exists():
        print("Opportunity Scanner is not installed.")
        return 1

    return subprocess.call(
        [sys.executable, str(SCANNER), *sys.argv[1:]],
        cwd=ROOT,
    )


if __name__ == "__main__":
    raise SystemExit(main())
PY

chmod +x "$COMPANYOS/opportunityctl"

echo "[6/9] Registering Opportunity Scanner..."

python - <<'PY'
import json
from pathlib import Path
from datetime import datetime, timezone

root = Path.home() / "companyos"
path = root / "ceo_memory" / "company_capabilities.json"

try:
    data = json.loads(path.read_text(encoding="utf-8"))
except Exception:
    data = {"capabilities": []}

if isinstance(data, list):
    capabilities = data
else:
    capabilities = data.setdefault("capabilities", [])

capability = {
    "id": "opportunity_discovery_scanner",
    "name": "Opportunity Discovery Scanner",
    "module": "agents.opportunity_scanner",
    "enabled": True,
    "mode": "internal",
    "automatic_external_research": False,
    "automatic_project_creation": False,
    "requires_owner_approval": True,
    "installed_at": datetime.now(timezone.utc).isoformat(),
}

capabilities[:] = [
    item for item in capabilities
    if not (
        isinstance(item, dict)
        and item.get("id") == "opportunity_discovery_scanner"
    )
]

capabilities.append(capability)

path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(data, indent=2), encoding="utf-8")

print("Opportunity Scanner registered.")
PY

echo "[7/9] Compiling Opportunity Scanner..."

python -m py_compile \
    "$AGENTS/opportunity_scanner.py" \
    "$COMPANYOS/opportunityctl"

echo "Opportunity Scanner compilation passed."

echo "[8/9] Running scanner tests..."

python "$COMPANYOS/opportunityctl" scan
python "$COMPANYOS/opportunityctl" status
python "$COMPANYOS/opportunityctl" list 5

echo "[9/9] Running CompanyOS verification..."

if [ -f "$COMPANYOS/verify.sh" ]; then
    bash "$COMPANYOS/verify.sh"
else
    echo "CompanyOS verify.sh not found."
    echo "Running Phase 15 verification instead..."

    python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"

required = [
    root / "agents" / "opportunity_scanner.py",
    root / "companyos" / "opportunityctl",
    root / "ceo_memory" / "opportunity_scanner_config.json",
    root / "ceo_memory" / "discovered_opportunities.json",
]

errors = []

for path in required:
    if not path.exists():
        errors.append(f"Missing: {path}")

for path in required[:2]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(f"Compile error {path}: {exc}")

try:
    data = json.loads(required[3].read_text(encoding="utf-8"))
    if not isinstance(data.get("opportunities"), list):
        errors.append("Opportunity memory has invalid structure")
except Exception as exc:
    errors.append(f"Opportunity memory error: {exc}")

print("--------------------------------------------")
print("Phase 15 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY
fi

echo
echo "============================================================"
echo " PHASE 15 STEP 1 INSTALLED"
echo "============================================================"
echo
echo "Opportunity Scanner:"
echo "  internal discovery: enabled"
echo "  external research: disabled"
echo "  automatic project creation: disabled"
echo "  automatic spending: disabled"
echo "  automatic publication: disabled"
echo
echo "Commands:"
echo "  python companyos/opportunityctl scan"
echo "  python companyos/opportunityctl status"
echo "  python companyos/opportunityctl list"
echo "  python companyos/opportunityctl show OPPORTUNITY_ID"
echo
echo "Memory:"
echo "  ceo_memory/discovered_opportunities.json"
echo "  ceo_memory/opportunity_scanner_health.json"
echo "  ceo_memory/opportunity_scanner_audit.json"
echo
