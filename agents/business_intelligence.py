#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "business_intelligence_config.json"
SNAPSHOT = MEMORY / "business_intelligence_snapshot.json"
HEALTH = MEMORY / "business_intelligence_health.json"
AUDIT = MEMORY / "business_intelligence_audit.json"

LEADS = MEMORY / "crm_leads.json"
QUOTES = MEMORY / "quote_registry.json"
PROJECTS = MEMORY / "project_registry.json"
MILESTONES = MEMORY / "project_milestones.json"
FOLLOWUPS = MEMORY / "sales_followups.json"
INVOICES = MEMORY / "invoice_registry.json"
PAYMENTS = MEMORY / "payment_registry.json"
EXPENSES = MEMORY / "expense_registry.json"
FINANCIAL_KPIS = MEMORY / "financial_kpis.json"
EXECUTIVE_SUMMARY = MEMORY / "daily_executive_summary.json"
ACTIVITY_FEED = MEMORY / "business_activity_feed.json"


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


def money(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except Exception:
        return 0.0


def build_recommendations(
    leads: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    followups: list[dict[str, Any]],
    invoices: list[dict[str, Any]],
    metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    recommendations = []

    pending_followups = [
        item for item in followups
        if item.get("status") == "pending"
    ]
    overdue_invoices = [
        item for item in invoices
        if item.get("status") in {"issued", "partially_paid"}
        and money(item.get("balance_due")) > 0
    ]
    stalled_projects = [
        item for item in projects
        if item.get("status") in {"planning", "waiting"}
        and int(item.get("progress_percent") or 0) < 25
    ]
    new_leads = [
        item for item in leads
        if item.get("status") == "new"
    ]

    if pending_followups:
        recommendations.append({
            "priority": "high",
            "type": "sales",
            "title": "Review pending follow-ups",
            "detail": f"{len(pending_followups)} follow-up(s) are waiting for owner review.",
            "external_action_required": False,
        })

    if overdue_invoices:
        recommendations.append({
            "priority": "high",
            "type": "finance",
            "title": "Review outstanding invoices",
            "detail": f"{len(overdue_invoices)} invoice(s) still have balances due.",
            "external_action_required": False,
        })

    if stalled_projects:
        recommendations.append({
            "priority": "medium",
            "type": "operations",
            "title": "Review stalled projects",
            "detail": f"{len(stalled_projects)} project(s) have low progress.",
            "external_action_required": False,
        })

    if new_leads:
        recommendations.append({
            "priority": "medium",
            "type": "crm",
            "title": "Qualify new leads",
            "detail": f"{len(new_leads)} new lead(s) need internal review.",
            "external_action_required": False,
        })

    if money(metrics.get("net_cash_position")) < 0:
        recommendations.append({
            "priority": "high",
            "type": "finance",
            "title": "Protect cash flow",
            "detail": "Recorded expenses currently exceed recorded payments.",
            "external_action_required": False,
        })

    if not recommendations:
        recommendations.append({
            "priority": "low",
            "type": "general",
            "title": "Company systems stable",
            "detail": "No major internal warnings detected.",
            "external_action_required": False,
        })

    return recommendations


def calculate_health(
    pending_followups: int,
    overdue_invoices: int,
    stalled_projects: int,
    net_cash: float,
) -> tuple[str, int]:
    score = 100
    score -= min(pending_followups * 5, 20)
    score -= min(overdue_invoices * 10, 30)
    score -= min(stalled_projects * 8, 24)

    if net_cash < 0:
        score -= 20

    score = max(0, min(100, score))

    if score >= 85:
        return "healthy", score
    if score >= 65:
        return "stable", score
    return "needs_review", score


def generate_snapshot() -> dict[str, Any]:
    config = load_json(CONFIG, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "business_intelligence_disabled",
        }
        audit("generate", result)
        return result

    leads = load_json(LEADS, {}).get("leads", [])
    quotes = load_json(QUOTES, {}).get("quotes", [])
    projects = load_json(PROJECTS, {}).get("projects", [])
    milestones = load_json(MILESTONES, {}).get("milestones", [])
    followups = load_json(FOLLOWUPS, {}).get("followups", [])
    invoices = load_json(INVOICES, {}).get("invoices", [])
    payments = load_json(PAYMENTS, {}).get("payments", [])
    expenses = load_json(EXPENSES, {}).get("expenses", [])
    financial_metrics = load_json(
        FINANCIAL_KPIS,
        {},
    ).get("metrics", {})
    executive_summary = load_json(
        EXECUTIVE_SUMMARY,
        {},
    ).get("summary", {})
    activity = load_json(
        ACTIVITY_FEED,
        {},
    ).get("activities", [])

    pipeline_value = sum(
        money(item.get("estimate_amount"))
        for item in leads
        if item.get("status") not in {"won", "lost"}
    )
    won_value = sum(
        money(item.get("estimate_amount"))
        for item in leads
        if item.get("status") == "won"
    )
    receivables = sum(
        money(item.get("balance_due"))
        for item in invoices
    )
    cash_received = sum(
        money(item.get("amount"))
        for item in payments
    )
    expense_total = sum(
        money(item.get("amount"))
        for item in expenses
    )
    net_cash = round(cash_received - expense_total, 2)

    pending_followups = sum(
        1 for item in followups
        if item.get("status") == "pending"
    )
    overdue_invoices = sum(
        1 for item in invoices
        if item.get("status") in {"issued", "partially_paid"}
        and money(item.get("balance_due")) > 0
    )
    stalled_projects = sum(
        1 for item in projects
        if item.get("status") in {"planning", "waiting"}
        and int(item.get("progress_percent") or 0) < 25
    )
    completed_milestones = sum(
        1 for item in milestones
        if item.get("status") == "completed"
    )

    company_health, company_score = calculate_health(
        pending_followups,
        overdue_invoices,
        stalled_projects,
        net_cash,
    )

    recommendations = build_recommendations(
        leads,
        projects,
        followups,
        invoices,
        financial_metrics,
    )

    snapshot = {
        "generated_at": now(),
        "company_health": company_health,
        "company_score": company_score,
        "crm": {
            "total_leads": len(leads),
            "new_leads": sum(
                1 for item in leads
                if item.get("status") == "new"
            ),
            "won_leads": sum(
                1 for item in leads
                if item.get("status") == "won"
            ),
            "lost_leads": sum(
                1 for item in leads
                if item.get("status") == "lost"
            ),
            "pipeline_value": round(pipeline_value, 2),
            "won_value": round(won_value, 2),
        },
        "sales": {
            "quote_count": len(quotes),
            "pending_followups": pending_followups,
            "conversion_rate_percent": (
                round(
                    (
                        sum(
                            1 for item in leads
                            if item.get("status") == "won"
                        )
                        / len(leads)
                    ) * 100,
                    2,
                )
                if leads
                else 0.0
            ),
        },
        "projects": {
            "total_projects": len(projects),
            "active_projects": sum(
                1 for item in projects
                if item.get("status") not in {"completed", "cancelled"}
            ),
            "stalled_projects": stalled_projects,
            "total_milestones": len(milestones),
            "completed_milestones": completed_milestones,
            "average_completion_percent": (
                round(
                    sum(
                        int(item.get("progress_percent") or 0)
                        for item in projects
                    ) / len(projects),
                    2,
                )
                if projects
                else 0.0
            ),
        },
        "finance": {
            "total_invoiced": round(
                sum(money(item.get("total")) for item in invoices),
                2,
            ),
            "cash_received": round(cash_received, 2),
            "accounts_receivable": round(receivables, 2),
            "recorded_expenses": round(expense_total, 2),
            "net_cash_position": net_cash,
            "overdue_invoice_count": overdue_invoices,
        },
        "warnings": {
            "pending_followups": pending_followups,
            "overdue_invoices": overdue_invoices,
            "stalled_projects": stalled_projects,
        },
        "recommendations": recommendations,
        "executive_summary": executive_summary,
        "recent_activity": activity[-10:],
        "automatic_external_execution": False,
        "automatic_publication": False,
        "automatic_spending": False,
    }

    save_json(
        SNAPSHOT,
        {
            "schema_version": 1,
            "snapshot": snapshot,
            "last_updated_at": now(),
        },
    )

    save_json(
        HEALTH,
        {
            "healthy": True,
            "company_health": company_health,
            "company_score": company_score,
            "last_generated_at": now(),
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "business_intelligence_snapshot_generated",
        "snapshot": snapshot,
    }

    audit("generate", result)
    return result


def show_snapshot() -> dict[str, Any]:
    store = load_json(SNAPSHOT, {})
    snapshot = store.get("snapshot")

    result = {
        "success": bool(snapshot),
        "status": "business_intelligence_snapshot",
        "snapshot": snapshot,
    }

    audit("show", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "business_intelligence_status",
        "enabled": config.get("enabled", False),
        "automatic_snapshot_generation": config.get(
            "automatic_snapshot_generation", False
        ),
        "automatic_internal_recommendations": config.get(
            "automatic_internal_recommendations", False
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
        "dashboard_host": config.get("dashboard_host"),
        "dashboard_port": config.get("dashboard_port"),
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
            return print_result(generate_snapshot())

        if action == "show":
            return print_result(show_snapshot())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_bi_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "business_intelligence_error",
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
