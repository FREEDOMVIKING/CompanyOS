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

CONFIG_PATH = MEMORY / "proposal_generator_config.json"
RANKINGS_PATH = MEMORY / "opportunity_rankings.json"
OPPORTUNITIES_PATH = MEMORY / "discovered_opportunities.json"
PROPOSALS_PATH = MEMORY / "project_proposals.json"
HEALTH_PATH = MEMORY / "proposal_generator_health.json"
AUDIT_PATH = MEMORY / "proposal_generator_audit.json"


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
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(value, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    temp.replace(path)


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


def proposal_id(opportunity_id: str) -> str:
    digest = hashlib.sha256(
        opportunity_id.encode("utf-8")
    ).hexdigest()[:12]

    return f"proposal-{digest}"


def get_opportunity(opportunity_id: str) -> dict[str, Any] | None:
    store = load_json(OPPORTUNITIES_PATH, {})

    for item in store.get("opportunities", []):
        if item.get("id") == opportunity_id:
            return item

    return None


def get_ranking(opportunity_id: str) -> dict[str, Any] | None:
    store = load_json(RANKINGS_PATH, {})

    for item in store.get("rankings", []):
        if item.get("opportunity_id") == opportunity_id:
            return item

    return None


def get_best_opportunity_id() -> str | None:
    store = load_json(RANKINGS_PATH, {})
    best = store.get("best_opportunity") or {}
    return best.get("opportunity_id")


def build_objectives(opportunity: dict[str, Any]) -> list[str]:
    title = opportunity.get("title", "Product")

    return [
        f"Validate demand for {title}",
        "Build a usable minimum viable product",
        "Create a repeatable customer acquisition process",
        "Test pricing with real prospective customers",
        "Measure usage, conversion and customer feedback",
    ]


def build_mvp_features(opportunity: dict[str, Any]) -> list[str]:
    category = opportunity.get("category")

    common = [
        "Simple mobile-friendly interface",
        "Customer or project record management",
        "Structured workflow and status tracking",
        "Exportable reports or documents",
        "Basic settings and configuration",
    ]

    category_features = {
        "local_services": [
            "Lead and customer tracking",
            "Bid and estimate status",
            "Follow-up reminders",
            "Job notes and activity history",
            "Basic sales pipeline dashboard",
        ],
        "small_business_tools": [
            "Guided data entry",
            "Reusable business templates",
            "Customer communication drafts",
            "Document generation",
            "Workflow history",
        ],
        "ai_automation": [
            "AI-assisted drafting",
            "Approval-controlled actions",
            "Prompt and response history",
            "Manual review queue",
            "Usage and quality tracking",
        ],
        "operations": [
            "Daily operational records",
            "Checklist and task workflow",
            "Report generation",
            "Photo or attachment references",
            "Supervisor review status",
        ],
        "developer_tools": [
            "Repository status inspection",
            "Change summary generation",
            "Release checklist",
            "Audit log",
            "Approval-controlled repository actions",
        ],
        "digital_products": [
            "Template catalog",
            "Guided customization",
            "Downloadable output",
            "Product version tracking",
            "Customer instructions",
        ],
    }

    return category_features.get(category, common)


def build_milestones(opportunity: dict[str, Any]) -> list[dict[str, Any]]:
    effort = int(opportunity.get("estimated_build_effort", 50))

    if effort <= 35:
        total_weeks = 2
    elif effort <= 50:
        total_weeks = 4
    elif effort <= 65:
        total_weeks = 6
    else:
        total_weeks = 8

    return [
        {
            "order": 1,
            "name": "Problem validation",
            "duration_days": max(2, total_weeks),
            "deliverables": [
                "Customer problem statement",
                "Target customer profile",
                "Initial pricing assumptions",
                "Go or hold validation decision"
            ]
        },
        {
            "order": 2,
            "name": "MVP design",
            "duration_days": max(3, total_weeks),
            "deliverables": [
                "MVP feature scope",
                "Core user workflow",
                "Data model",
                "Prototype plan"
            ]
        },
        {
            "order": 3,
            "name": "MVP build",
            "duration_days": total_weeks * 4,
            "deliverables": [
                "Working core product",
                "Basic testing",
                "Local deployment",
                "Internal documentation"
            ]
        },
        {
            "order": 4,
            "name": "Pilot and feedback",
            "duration_days": 7,
            "deliverables": [
                "Pilot user feedback",
                "Issue list",
                "Pricing feedback",
                "Launch recommendation"
            ]
        },
    ]


def build_risks(
    opportunity: dict[str, Any],
    ranking: dict[str, Any],
) -> list[dict[str, str]]:
    risks = [
        {
            "risk": "Customer demand may be weaker than estimated",
            "mitigation": "Validate with prospective customers before full build"
        },
        {
            "risk": "MVP scope may grow too large",
            "mitigation": "Limit the first release to essential workflows"
        },
        {
            "risk": "Customers may resist subscription pricing",
            "mitigation": "Test setup-fee and subscription pricing options"
        },
        {
            "risk": "Product may require external integrations",
            "mitigation": "Begin with local and approval-controlled workflows"
        },
    ]

    if ranking.get("risk_level") in {"high", "very_high"}:
        risks.append({
            "risk": "Execution risk is above the preferred level",
            "mitigation": "Use a smaller proof of concept before committing resources"
        })

    if int(opportunity.get("estimated_build_effort", 0)) >= 60:
        risks.append({
            "risk": "Build effort may delay customer testing",
            "mitigation": "Separate must-have features from later releases"
        })

    return risks


def build_assumptions(opportunity: dict[str, Any]) -> list[str]:
    return [
        "The target customer experiences the stated problem regularly",
        "The customer is willing to use a mobile or web-based workflow",
        "A focused MVP can be built without paid infrastructure",
        "Early customer testing can be performed before public launch",
        f"The proposed revenue model is {opportunity.get('revenue_model')}",
    ]


def build_revenue_hypothesis(
    opportunity: dict[str, Any],
) -> dict[str, Any]:
    revenue_model = str(opportunity.get("revenue_model", "")).lower()

    if "subscription" in revenue_model:
        pricing = {
            "entry_price_monthly": 19,
            "target_price_monthly": 39,
            "premium_price_monthly": 79,
        }
        example = {
            "10_customers_monthly": 390,
            "25_customers_monthly": 975,
            "100_customers_monthly": 3900,
        }
    elif "setup fee" in revenue_model:
        pricing = {
            "basic_setup_fee": 199,
            "standard_setup_fee": 499,
            "support_plan_monthly": 49,
        }
        example = {
            "5_standard_setups": 2495,
            "10_support_customers_monthly": 490,
        }
    else:
        pricing = {
            "basic_product_price": 29,
            "standard_product_price": 59,
            "premium_product_price": 99,
        }
        example = {
            "10_standard_sales": 590,
            "50_standard_sales": 2950,
            "100_standard_sales": 5900,
        }

    return {
        "model": opportunity.get("revenue_model"),
        "pricing_hypothesis": pricing,
        "example_revenue": example,
        "financial_projection_is_estimate": True,
        "requires_market_validation": True,
    }


def update_statistics(store: dict[str, Any]) -> None:
    proposals = store.get("proposals", [])

    store["statistics"] = {
        "total": len(proposals),
        "pending_owner_approval": sum(
            1 for item in proposals
            if item.get("status") == "pending_owner_approval"
        ),
        "approved": sum(
            1 for item in proposals
            if item.get("status") == "approved"
        ),
        "rejected": sum(
            1 for item in proposals
            if item.get("status") == "rejected"
        ),
        "handed_to_factory": sum(
            1 for item in proposals
            if item.get("status") == "handed_to_factory"
        ),
    }

    store["last_updated_at"] = now()


def generate(opportunity_id: str) -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "proposal_generator_disabled",
        }
        audit("generate", result)
        return result

    opportunity = get_opportunity(opportunity_id)
    ranking = get_ranking(opportunity_id)

    if not opportunity:
        result = {
            "success": False,
            "status": "opportunity_not_found",
            "opportunity_id": opportunity_id,
        }
        audit("generate", result)
        return result

    if not ranking:
        result = {
            "success": False,
            "status": "opportunity_not_scored",
            "opportunity_id": opportunity_id,
            "next_command": "python companyos/scorectl score",
        }
        audit("generate", result)
        return result

    store = load_json(
        PROPOSALS_PATH,
        {
            "schema_version": 1,
            "proposals": [],
            "statistics": {},
            "last_updated_at": None,
        },
    )

    proposals = store.setdefault("proposals", [])
    item_id = proposal_id(opportunity_id)

    for existing in proposals:
        if existing.get("id") == item_id:
            result = {
                "success": True,
                "status": "proposal_already_exists",
                "proposal": existing,
            }
            audit("generate", result)
            return result

    proposal = {
        "id": item_id,
        "opportunity_id": opportunity_id,
        "title": opportunity.get("title"),
        "proposal_title": (
            f"Business Proposal: {opportunity.get('title')}"
        ),
        "status": config.get(
            "default_proposal_status",
            "pending_owner_approval",
        ),
        "owner_approval_required": True,
        "approved_by_owner": False,
        "factory_handoff_status": "not_started",
        "executive_summary": (
            f"{opportunity.get('title')} is a proposed "
            f"{opportunity.get('category')} product for "
            f"{opportunity.get('target_customer')}. "
            f"It addresses the problem that "
            f"{opportunity.get('problem')} "
            f"The proposed solution is: "
            f"{opportunity.get('solution')}"
        ),
        "customer_problem": opportunity.get("problem"),
        "proposed_solution": opportunity.get("solution"),
        "target_customer": opportunity.get("target_customer"),
        "revenue_model": opportunity.get("revenue_model"),
        "priority_score": ranking.get("priority_score"),
        "confidence_score": ranking.get("confidence_score"),
        "recommendation": ranking.get("recommendation"),
        "risk_level": ranking.get("risk_level"),
        "estimated_launch_window": ranking.get(
            "estimated_launch_window"
        ),
        "strategic_reasons": ranking.get("reasons", []),
        "objectives": build_objectives(opportunity),
        "mvp_features": build_mvp_features(opportunity),
        "milestones": build_milestones(opportunity),
        "revenue_hypothesis": build_revenue_hypothesis(opportunity),
        "risks": build_risks(opportunity, ranking),
        "assumptions": build_assumptions(opportunity),
        "go_hold_recommendation": (
            "go"
            if ranking.get("recommendation") == "recommended"
            else "hold_for_validation"
        ),
        "automatic_spending": False,
        "automatic_publication": False,
        "automatic_project_creation": False,
        "created_at": now(),
        "updated_at": now(),
    }

    proposals.append(proposal)
    update_statistics(store)
    save_json(PROPOSALS_PATH, store)

    opportunities_store = load_json(OPPORTUNITIES_PATH, {})

    for item in opportunities_store.get("opportunities", []):
        if item.get("id") == opportunity_id:
            item["proposal_status"] = "created"
            item["proposal_id"] = item_id
            item["updated_at"] = now()

    save_json(OPPORTUNITIES_PATH, opportunities_store)

    health = {
        "healthy": True,
        "last_generated_at": now(),
        "last_error": None,
        "total_proposals": len(proposals),
        "latest_proposal_id": item_id,
    }
    save_json(HEALTH_PATH, health)

    result = {
        "success": True,
        "status": "proposal_generated",
        "proposal_id": item_id,
        "opportunity_id": opportunity_id,
        "title": proposal["title"],
        "proposal_status": proposal["status"],
        "priority_score": proposal["priority_score"],
        "recommendation": proposal["recommendation"],
        "owner_approval_required": True,
        "automatic_project_creation": False,
        "automatic_spending": False,
        "automatic_publication": False,
    }

    audit("generate", result)
    return result


def generate_best() -> dict[str, Any]:
    opportunity_id = get_best_opportunity_id()

    if not opportunity_id:
        result = {
            "success": False,
            "status": "best_opportunity_unavailable",
            "next_command": "python companyos/scorectl score",
        }
        audit("generate_best", result)
        return result

    return generate(opportunity_id)


def list_proposals(limit: int = 20) -> dict[str, Any]:
    store = load_json(PROPOSALS_PATH, {})
    proposals = store.get("proposals", [])
    limit = max(1, min(limit, 100))

    result = {
        "success": True,
        "status": "proposal_list",
        "total": len(proposals),
        "count": min(limit, len(proposals)),
        "statistics": store.get("statistics", {}),
        "proposals": [
            {
                "id": item.get("id"),
                "opportunity_id": item.get("opportunity_id"),
                "title": item.get("title"),
                "status": item.get("status"),
                "priority_score": item.get("priority_score"),
                "recommendation": item.get("recommendation"),
                "go_hold_recommendation": item.get(
                    "go_hold_recommendation"
                ),
            }
            for item in proposals[:limit]
        ],
    }

    audit("list", result)
    return result


def show(proposal_id_value: str) -> dict[str, Any]:
    store = load_json(PROPOSALS_PATH, {})

    for proposal in store.get("proposals", []):
        if proposal.get("id") == proposal_id_value:
            result = {
                "success": True,
                "status": "proposal_details",
                "proposal": proposal,
            }
            audit("show", result)
            return result

    result = {
        "success": False,
        "status": "proposal_not_found",
        "proposal_id": proposal_id_value,
    }

    audit("show", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})
    store = load_json(PROPOSALS_PATH, {})
    health = load_json(HEALTH_PATH, {})

    result = {
        "success": True,
        "status": "proposal_generator_status",
        "enabled": config.get("enabled", False),
        "healthy": health.get("healthy", False),
        "statistics": store.get("statistics", {}),
        "last_updated_at": store.get("last_updated_at"),
        "automatic_generation": config.get(
            "automatic_generation",
            False,
        ),
        "automatic_approval": config.get(
            "automatic_approval",
            False,
        ),
        "automatic_project_creation": config.get(
            "automatic_project_creation",
            False,
        ),
        "automatic_factory_handoff": config.get(
            "automatic_factory_handoff",
            False,
        ),
        "owner_approval_required": config.get(
            "owner_approval_required",
            True,
        ),
    }

    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: proposal_generator.py "
            "generate <opportunity_id>|generate-best|"
            "status|list [limit]|show <proposal_id>"
        )
        return 2

    action = sys.argv[1].lower()

    try:
        if action == "generate":
            if len(sys.argv) < 3:
                raise ValueError("Opportunity ID is required")
            return print_result(generate(sys.argv[2]))

        if action == "generate-best":
            return print_result(generate_best())

        if action == "status":
            return print_result(status())

        if action == "list":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            return print_result(list_proposals(limit))

        if action == "show":
            if len(sys.argv) < 3:
                raise ValueError("Proposal ID is required")
            return print_result(show(sys.argv[2]))

        return print_result({
            "success": False,
            "status": "unknown_proposal_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "proposal_generator_error",
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
