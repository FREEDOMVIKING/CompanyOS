#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"

CONFIG = MEMORY / "sales_pipeline_config.json"
LEADS = MEMORY / "crm_leads.json"
QUOTES = MEMORY / "quote_registry.json"
FOLLOWUPS = MEMORY / "sales_followups.json"
METRICS = MEMORY / "sales_pipeline_metrics.json"
HEALTH = MEMORY / "sales_pipeline_health.json"
AUDIT = MEMORY / "sales_pipeline_audit.json"


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


def make_id(prefix: str, seed: str) -> str:
    digest = hashlib.sha256(
        f"{seed}:{now()}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{prefix}-{digest}"


def find_lead(lead_id: str) -> dict[str, Any] | None:
    for lead in load_json(LEADS, {}).get("leads", []):
        if lead.get("id") == lead_id:
            return lead
    return None


def latest_lead() -> dict[str, Any] | None:
    leads = load_json(LEADS, {}).get("leads", [])
    return leads[-1] if leads else None


def update_followup_statistics(store: dict[str, Any]) -> None:
    records = store.get("followups", [])
    store["statistics"] = {
        "total": len(records),
        "pending": sum(
            1 for item in records
            if item.get("status") == "pending"
        ),
        "completed": sum(
            1 for item in records
            if item.get("status") == "completed"
        ),
        "cancelled": sum(
            1 for item in records
            if item.get("status") == "cancelled"
        ),
    }
    store["last_updated_at"] = now()


def schedule_followup(
    lead_id: str,
    due_date: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    config = load_json(CONFIG, {})
    lead = find_lead(lead_id)

    if not lead:
        result = {
            "success": False,
            "status": "lead_not_found",
            "lead_id": lead_id,
        }
        audit("schedule_followup", result)
        return result

    if due_date is None:
        days = int(config.get("default_follow_up_days", 3))
        due_date = (
            datetime.now(timezone.utc) + timedelta(days=days)
        ).date().isoformat()

    store = load_json(
        FOLLOWUPS,
        {
            "schema_version": 1,
            "followups": [],
            "statistics": {},
        },
    )

    record = {
        "id": make_id("followup", lead_id),
        "lead_id": lead_id,
        "customer_name": lead.get("customer_name"),
        "project_name": lead.get("project_name"),
        "due_date": due_date,
        "note": note or "Review lead and prepare owner-approved follow-up.",
        "status": "pending",
        "external_contact_authorized": False,
        "automatic_email": False,
        "automatic_sms": False,
        "created_at": now(),
        "updated_at": now(),
    }

    store.setdefault("followups", []).append(record)
    update_followup_statistics(store)
    save_json(FOLLOWUPS, store)

    result = {
        "success": True,
        "status": "followup_scheduled",
        "followup": record,
        "automatic_customer_contact": False,
    }

    audit("schedule_followup", result)
    return result


def schedule_latest() -> dict[str, Any]:
    lead = latest_lead()

    if not lead:
        result = {
            "success": False,
            "status": "no_leads_available",
        }
        audit("schedule_latest", result)
        return result

    return schedule_followup(str(lead.get("id")))


def complete_followup(
    followup_id: str,
    result_note: str | None = None,
) -> dict[str, Any]:
    store = load_json(FOLLOWUPS, {})

    for item in store.get("followups", []):
        if item.get("id") != followup_id:
            continue

        item["status"] = "completed"
        item["result_note"] = result_note
        item["completed_at"] = now()
        item["updated_at"] = now()

        update_followup_statistics(store)
        save_json(FOLLOWUPS, store)

        result = {
            "success": True,
            "status": "followup_completed",
            "followup_id": followup_id,
            "result_note": result_note,
        }

        audit("complete_followup", result)
        return result

    result = {
        "success": False,
        "status": "followup_not_found",
        "followup_id": followup_id,
    }

    audit("complete_followup", result)
    return result


def calculate_metrics() -> dict[str, Any]:
    leads = load_json(LEADS, {}).get("leads", [])
    quotes = load_json(QUOTES, {}).get("quotes", [])
    followups = load_json(FOLLOWUPS, {}).get("followups", [])

    total_leads = len(leads)
    won = sum(1 for item in leads if item.get("status") == "won")
    lost = sum(1 for item in leads if item.get("status") == "lost")
    qualified = sum(
        1 for item in leads
        if item.get("status") in {
            "qualified",
            "proposal_sent",
            "won",
        }
    )
    proposal_sent = sum(
        1 for item in leads
        if item.get("status") in {
            "proposal_sent",
            "won",
        }
    )

    pipeline_value = sum(
        float(item.get("estimate_amount") or 0)
        for item in leads
        if item.get("status") not in {"won", "lost"}
    )

    won_value = sum(
        float(item.get("estimate_amount") or 0)
        for item in leads
        if item.get("status") == "won"
    )

    quote_value = sum(
        float(item.get("amount") or 0)
        for item in quotes
        if item.get("status") in {"draft", "approved", "sent", "accepted"}
    )

    conversion_rate = (
        round((won / total_leads) * 100, 2)
        if total_leads
        else 0.0
    )

    qualification_rate = (
        round((qualified / total_leads) * 100, 2)
        if total_leads
        else 0.0
    )

    proposal_rate = (
        round((proposal_sent / total_leads) * 100, 2)
        if total_leads
        else 0.0
    )

    pending_followups = sum(
        1 for item in followups
        if item.get("status") == "pending"
    )

    metrics = {
        "total_leads": total_leads,
        "qualified_leads": qualified,
        "proposals_sent": proposal_sent,
        "won_leads": won,
        "lost_leads": lost,
        "conversion_rate_percent": conversion_rate,
        "qualification_rate_percent": qualification_rate,
        "proposal_rate_percent": proposal_rate,
        "active_pipeline_value": round(pipeline_value, 2),
        "won_revenue_value": round(won_value, 2),
        "open_quote_value": round(quote_value, 2),
        "pending_followups": pending_followups,
        "forecast_value": round(
            pipeline_value * 0.35 + won_value,
            2,
        ),
        "calculated_at": now(),
    }

    save_json(
        METRICS,
        {
            "schema_version": 1,
            "metrics": metrics,
            "last_updated_at": now(),
        },
    )

    save_json(
        HEALTH,
        {
            "healthy": True,
            "last_calculated_at": now(),
            "last_error": None,
        },
    )

    result = {
        "success": True,
        "status": "sales_metrics_calculated",
        "metrics": metrics,
    }

    audit("metrics", result)
    return result


def list_followups() -> dict[str, Any]:
    store = load_json(FOLLOWUPS, {})

    result = {
        "success": True,
        "status": "followup_list",
        "count": len(store.get("followups", [])),
        "statistics": store.get("statistics", {}),
        "followups": store.get("followups", []),
    }

    audit("followups", result)
    return result


def pipeline() -> dict[str, Any]:
    leads = load_json(LEADS, {}).get("leads", [])

    grouped: dict[str, list[dict[str, Any]]] = {}

    for lead in leads:
        grouped.setdefault(
            str(lead.get("status", "unknown")),
            [],
        ).append(lead)

    result = {
        "success": True,
        "status": "sales_pipeline",
        "stages": grouped,
        "total_leads": len(leads),
    }

    audit("pipeline", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    followups = load_json(FOLLOWUPS, {})
    metrics = load_json(METRICS, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "sales_pipeline_status",
        "enabled": config.get("enabled", False),
        "automatic_follow_up_scheduling": config.get(
            "automatic_follow_up_scheduling", False
        ),
        "automatic_customer_contact": config.get(
            "automatic_customer_contact", False
        ),
        "automatic_email": config.get("automatic_email", False),
        "automatic_sms": config.get("automatic_sms", False),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "followup_statistics": followups.get("statistics", {}),
        "metrics": metrics.get("metrics", {}),
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
        if action == "schedule":
            if len(sys.argv) < 3:
                raise ValueError("Lead ID is required")

            due = sys.argv[3] if len(sys.argv) > 3 else None
            note = " ".join(sys.argv[4:]).strip() or None

            return print_result(
                schedule_followup(sys.argv[2], due, note)
            )

        if action == "schedule-latest":
            return print_result(schedule_latest())

        if action == "complete":
            if len(sys.argv) < 3:
                raise ValueError("Follow-up ID is required")

            note = " ".join(sys.argv[3:]).strip() or None

            return print_result(
                complete_followup(sys.argv[2], note)
            )

        if action == "metrics":
            return print_result(calculate_metrics())

        if action == "followups":
            return print_result(list_followups())

        if action == "pipeline":
            return print_result(pipeline())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_sales_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "sales_pipeline_error",
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
