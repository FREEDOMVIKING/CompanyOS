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

CONFIG = MEMORY / "crm_config.json"
CUSTOMERS = MEMORY / "crm_customers.json"
LEADS = MEMORY / "crm_leads.json"
ACTIVITIES = MEMORY / "crm_activities.json"
HEALTH = MEMORY / "crm_health.json"
AUDIT = MEMORY / "crm_audit.json"


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


def short_id(prefix: str, seed: str) -> str:
    digest = hashlib.sha256(
        f"{seed}:{now()}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{prefix}-{digest}"


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


def add_activity(
    activity_type: str,
    entity_type: str,
    entity_id: str,
    note: str,
) -> None:
    store = load_json(
        ACTIVITIES,
        {
            "schema_version": 1,
            "activities": [],
            "last_updated_at": None,
        },
    )

    records = store.setdefault("activities", [])
    records.append({
        "id": short_id("activity", entity_id),
        "activity_type": activity_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "note": note,
        "created_at": now(),
    })

    store["last_updated_at"] = now()
    save_json(ACTIVITIES, store)


def update_customer_stats(store: dict[str, Any]) -> None:
    customers = store.get("customers", [])

    store["statistics"] = {
        "total": len(customers),
        "active": sum(
            1 for item in customers
            if item.get("status") == "active"
        ),
        "inactive": sum(
            1 for item in customers
            if item.get("status") == "inactive"
        ),
    }
    store["last_updated_at"] = now()


def update_lead_stats(store: dict[str, Any]) -> None:
    leads = store.get("leads", [])
    statuses = [
        "new",
        "contacted",
        "qualified",
        "proposal_sent",
        "won",
        "lost",
        "hold",
    ]

    stats = {"total": len(leads)}
    for status in statuses:
        stats[status] = sum(
            1 for item in leads
            if item.get("status") == status
        )

    store["statistics"] = stats
    store["last_updated_at"] = now()


def add_customer(
    name: str,
    phone: str | None = None,
    email: str | None = None,
    address: str | None = None,
) -> dict[str, Any]:
    if not name.strip():
        return {
            "success": False,
            "status": "customer_name_required",
        }

    store = load_json(
        CUSTOMERS,
        {
            "schema_version": 1,
            "customers": [],
            "statistics": {},
        },
    )

    customer = {
        "id": short_id("customer", name),
        "name": name.strip(),
        "phone": phone,
        "email": email,
        "address": address,
        "status": "active",
        "created_at": now(),
        "updated_at": now(),
    }

    store.setdefault("customers", []).append(customer)
    update_customer_stats(store)
    save_json(CUSTOMERS, store)

    add_activity(
        "customer_created",
        "customer",
        customer["id"],
        f"Customer created: {customer['name']}",
    )

    result = {
        "success": True,
        "status": "customer_created",
        "customer": customer,
    }
    audit("add_customer", result)
    return result


def add_lead(
    customer_name: str,
    project_name: str,
    estimate_amount: float | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    if not customer_name.strip():
        return {
            "success": False,
            "status": "lead_customer_name_required",
        }

    if not project_name.strip():
        return {
            "success": False,
            "status": "lead_project_name_required",
        }

    store = load_json(
        LEADS,
        {
            "schema_version": 1,
            "leads": [],
            "statistics": {},
        },
    )

    lead = {
        "id": short_id("lead", f"{customer_name}:{project_name}"),
        "customer_name": customer_name.strip(),
        "project_name": project_name.strip(),
        "estimate_amount": estimate_amount,
        "source": source or "manual",
        "status": "new",
        "follow_up_date": None,
        "notes": [],
        "external_contact_authorized": False,
        "created_at": now(),
        "updated_at": now(),
    }

    store.setdefault("leads", []).append(lead)
    update_lead_stats(store)
    save_json(LEADS, store)

    add_activity(
        "lead_created",
        "lead",
        lead["id"],
        f"Lead created for {lead['customer_name']}",
    )

    result = {
        "success": True,
        "status": "lead_created",
        "lead": lead,
        "automatic_external_contact": False,
    }
    audit("add_lead", result)
    return result


def update_lead_status(
    lead_id: str,
    new_status: str,
    note: str | None = None,
) -> dict[str, Any]:
    config = load_json(CONFIG, {})
    allowed = set(config.get("lead_statuses", []))

    if new_status not in allowed:
        result = {
            "success": False,
            "status": "invalid_lead_status",
            "allowed_statuses": sorted(allowed),
        }
        audit("update_status", result)
        return result

    store = load_json(LEADS, {})

    for lead in store.get("leads", []):
        if lead.get("id") != lead_id:
            continue

        previous = lead.get("status")
        lead["status"] = new_status
        lead["updated_at"] = now()

        if note:
            lead.setdefault("notes", []).append({
                "note": note,
                "created_at": now(),
            })

        update_lead_stats(store)
        save_json(LEADS, store)

        add_activity(
            "lead_status_changed",
            "lead",
            lead_id,
            f"{previous} -> {new_status}"
            + (f": {note}" if note else ""),
        )

        result = {
            "success": True,
            "status": "lead_status_updated",
            "lead_id": lead_id,
            "previous_status": previous,
            "new_status": new_status,
        }
        audit("update_status", result)
        return result

    result = {
        "success": False,
        "status": "lead_not_found",
        "lead_id": lead_id,
    }
    audit("update_status", result)
    return result


def set_follow_up(
    lead_id: str,
    follow_up_date: str,
    note: str | None = None,
) -> dict[str, Any]:
    store = load_json(LEADS, {})

    for lead in store.get("leads", []):
        if lead.get("id") != lead_id:
            continue

        lead["follow_up_date"] = follow_up_date
        lead["updated_at"] = now()

        if note:
            lead.setdefault("notes", []).append({
                "note": note,
                "created_at": now(),
            })

        update_lead_stats(store)
        save_json(LEADS, store)

        add_activity(
            "follow_up_scheduled",
            "lead",
            lead_id,
            f"Follow-up scheduled for {follow_up_date}",
        )

        result = {
            "success": True,
            "status": "follow_up_scheduled",
            "lead_id": lead_id,
            "follow_up_date": follow_up_date,
            "automatic_follow_up": False,
        }
        audit("follow_up", result)
        return result

    result = {
        "success": False,
        "status": "lead_not_found",
        "lead_id": lead_id,
    }
    audit("follow_up", result)
    return result


def list_customers() -> dict[str, Any]:
    store = load_json(CUSTOMERS, {})
    result = {
        "success": True,
        "status": "customer_list",
        "count": len(store.get("customers", [])),
        "statistics": store.get("statistics", {}),
        "customers": store.get("customers", []),
    }
    audit("customers", result)
    return result


def list_leads() -> dict[str, Any]:
    store = load_json(LEADS, {})
    result = {
        "success": True,
        "status": "lead_list",
        "count": len(store.get("leads", [])),
        "statistics": store.get("statistics", {}),
        "leads": store.get("leads", []),
    }
    audit("leads", result)
    return result


def list_activities() -> dict[str, Any]:
    store = load_json(ACTIVITIES, {})
    result = {
        "success": True,
        "status": "crm_activity_list",
        "count": len(store.get("activities", [])),
        "activities": store.get("activities", []),
    }
    audit("activities", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    customers = load_json(CUSTOMERS, {})
    leads = load_json(LEADS, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "crm_status",
        "enabled": config.get("enabled", False),
        "automatic_follow_up": config.get(
            "automatic_follow_up", False
        ),
        "automatic_email": config.get("automatic_email", False),
        "automatic_sms": config.get("automatic_sms", False),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "customer_statistics": customers.get("statistics", {}),
        "lead_statistics": leads.get("statistics", {}),
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
        if action == "add-customer":
            if len(sys.argv) < 3:
                raise ValueError("Customer name is required")

            name = sys.argv[2]
            phone = sys.argv[3] if len(sys.argv) > 3 else None
            email = sys.argv[4] if len(sys.argv) > 4 else None
            address = sys.argv[5] if len(sys.argv) > 5 else None

            return print_result(
                add_customer(name, phone, email, address)
            )

        if action == "add-lead":
            if len(sys.argv) < 4:
                raise ValueError(
                    "Customer name and project name are required"
                )

            estimate = (
                float(sys.argv[4])
                if len(sys.argv) > 4
                else None
            )
            source = sys.argv[5] if len(sys.argv) > 5 else None

            return print_result(
                add_lead(
                    sys.argv[2],
                    sys.argv[3],
                    estimate,
                    source,
                )
            )

        if action == "set-status":
            if len(sys.argv) < 4:
                raise ValueError("Lead ID and status are required")

            note = " ".join(sys.argv[4:]).strip() or None
            return print_result(
                update_lead_status(
                    sys.argv[2],
                    sys.argv[3],
                    note,
                )
            )

        if action == "follow-up":
            if len(sys.argv) < 4:
                raise ValueError(
                    "Lead ID and follow-up date are required"
                )

            note = " ".join(sys.argv[4:]).strip() or None
            return print_result(
                set_follow_up(
                    sys.argv[2],
                    sys.argv[3],
                    note,
                )
            )

        if action == "customers":
            return print_result(list_customers())

        if action == "leads":
            return print_result(list_leads())

        if action == "activities":
            return print_result(list_activities())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_crm_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "crm_error",
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
