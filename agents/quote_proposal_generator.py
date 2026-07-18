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
WORKSPACE = ROOT / "workspace" / "quotes"

CONFIG = MEMORY / "quote_config.json"
LEADS = MEMORY / "crm_leads.json"
REGISTRY = MEMORY / "quote_registry.json"
HEALTH = MEMORY / "quote_health.json"
AUDIT = MEMORY / "quote_audit.json"


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


def short_id(prefix: str, seed: str) -> str:
    digest = hashlib.sha256(
        f"{seed}:{now()}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{prefix}-{digest}"


def safe_name(value: str) -> str:
    text = "".join(
        c.lower() if c.isalnum() else "_"
        for c in value
    )
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_") or "quote"


def find_lead(lead_id: str) -> dict[str, Any] | None:
    for lead in load_json(LEADS, {}).get("leads", []):
        if lead.get("id") == lead_id:
            return lead
    return None


def latest_lead() -> dict[str, Any] | None:
    leads = load_json(LEADS, {}).get("leads", [])
    return leads[-1] if leads else None


def update_statistics(store: dict[str, Any]) -> None:
    quotes = store.get("quotes", [])
    statuses = [
        "draft",
        "approved",
        "sent",
        "accepted",
        "rejected",
    ]

    stats = {"total": len(quotes)}
    for status in statuses:
        stats[status] = sum(
            1 for item in quotes
            if item.get("status") == status
        )

    store["statistics"] = stats
    store["last_updated_at"] = now()


def build_markdown(quote: dict[str, Any]) -> str:
    amount = quote.get("amount")
    amount_text = (
        f"${amount:,.2f}"
        if isinstance(amount, (int, float))
        else "To be determined"
    )

    return f"""# Project Quote

Quote ID: {quote['id']}
Customer: {quote['customer_name']}
Project: {quote['project_name']}
Status: {quote['status']}
Created: {quote['created_at']}
Valid until: {quote['valid_until']}

## Scope of Work

{quote['scope']}

## Price

Estimated total: {amount_text}

## Terms

- Quote is valid until {quote['valid_until']}.
- Final scope changes may affect price.
- Scheduling begins after owner approval and customer acceptance.
- External delivery has not been authorized.
- No automatic payment collection is enabled.

## Internal Approval

Owner approval required before sending: Yes
Automatic email: Disabled
Automatic SMS: Disabled
Automatic external execution: Disabled
"""


def generate(
    lead_id: str,
    scope: str | None = None,
) -> dict[str, Any]:
    config = load_json(CONFIG, {})
    lead = find_lead(lead_id)

    if not lead:
        result = {
            "success": False,
            "status": "lead_not_found",
            "lead_id": lead_id,
        }
        audit("generate", result)
        return result

    valid_days = int(config.get("default_valid_days", 30))
    created = datetime.now(timezone.utc)
    valid_until = (created + timedelta(days=valid_days)).date().isoformat()

    quote = {
        "id": short_id("quote", lead_id),
        "lead_id": lead_id,
        "customer_name": lead.get("customer_name"),
        "project_name": lead.get("project_name"),
        "amount": lead.get("estimate_amount"),
        "scope": (
            scope
            or f"Provide labor, materials, coordination and completion "
               f"for {lead.get('project_name')}."
        ),
        "currency": config.get("default_currency", "USD"),
        "status": "draft",
        "owner_approved": False,
        "customer_delivery_authorized": False,
        "automatic_email": False,
        "automatic_sms": False,
        "automatic_external_execution": False,
        "created_at": created.isoformat(),
        "valid_until": valid_until,
        "updated_at": created.isoformat(),
    }

    quote_dir = WORKSPACE / safe_name(quote["id"])
    quote_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = quote_dir / "QUOTE.md"
    json_path = quote_dir / "QUOTE.json"

    markdown_path.write_text(
        build_markdown(quote),
        encoding="utf-8",
    )

    json_path.write_text(
        json.dumps(quote, indent=2),
        encoding="utf-8",
    )

    quote["markdown_path"] = str(markdown_path)
    quote["json_path"] = str(json_path)

    store = load_json(
        REGISTRY,
        {
            "schema_version": 1,
            "quotes": [],
            "statistics": {},
        },
    )

    store.setdefault("quotes", []).append(quote)
    update_statistics(store)
    save_json(REGISTRY, store)

    save_json(
        HEALTH,
        {
            "healthy": True,
            "latest_quote_id": quote["id"],
            "latest_quote_path": str(markdown_path),
            "last_error": None,
            "updated_at": now(),
        },
    )

    result = {
        "success": True,
        "status": "quote_generated",
        "quote_id": quote["id"],
        "lead_id": lead_id,
        "customer_name": quote["customer_name"],
        "project_name": quote["project_name"],
        "amount": quote["amount"],
        "markdown_path": str(markdown_path),
        "owner_approval_required": True,
        "automatic_customer_delivery": False,
        "automatic_email": False,
        "automatic_sms": False,
    }

    audit("generate", result)
    return result


def generate_latest() -> dict[str, Any]:
    lead = latest_lead()
    if not lead:
        result = {
            "success": False,
            "status": "no_leads_available",
        }
        audit("generate_latest", result)
        return result

    return generate(str(lead.get("id")))


def approve(quote_id: str, reason: str | None) -> dict[str, Any]:
    store = load_json(REGISTRY, {})

    for quote in store.get("quotes", []):
        if quote.get("id") != quote_id:
            continue

        quote["status"] = "approved"
        quote["owner_approved"] = True
        quote["approval_reason"] = reason
        quote["approved_at"] = now()
        quote["updated_at"] = now()

        update_statistics(store)
        save_json(REGISTRY, store)

        result = {
            "success": True,
            "status": "quote_approved",
            "quote_id": quote_id,
            "reason": reason,
            "customer_delivery_authorized": False,
        }

        audit("approve", result)
        return result

    result = {
        "success": False,
        "status": "quote_not_found",
        "quote_id": quote_id,
    }
    audit("approve", result)
    return result


def list_quotes() -> dict[str, Any]:
    store = load_json(REGISTRY, {})
    result = {
        "success": True,
        "status": "quote_list",
        "count": len(store.get("quotes", [])),
        "statistics": store.get("statistics", {}),
        "quotes": store.get("quotes", []),
    }
    audit("list", result)
    return result


def latest_quote() -> dict[str, Any]:
    quotes = load_json(REGISTRY, {}).get("quotes", [])
    result = {
        "success": bool(quotes),
        "status": "latest_quote",
        "quote": quotes[-1] if quotes else None,
    }
    audit("latest", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    registry = load_json(REGISTRY, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "quote_generator_status",
        "enabled": config.get("enabled", False),
        "automatic_quote_generation": config.get(
            "automatic_quote_generation", False
        ),
        "automatic_customer_delivery": config.get(
            "automatic_customer_delivery", False
        ),
        "automatic_email": config.get("automatic_email", False),
        "automatic_sms": config.get("automatic_sms", False),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "statistics": registry.get("statistics", {}),
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
            if len(sys.argv) < 3:
                raise ValueError("Lead ID is required")

            scope = " ".join(sys.argv[3:]).strip() or None
            return print_result(generate(sys.argv[2], scope))

        if action == "generate-latest":
            return print_result(generate_latest())

        if action == "approve":
            if len(sys.argv) < 3:
                raise ValueError("Quote ID is required")

            reason = " ".join(sys.argv[3:]).strip() or None
            return print_result(approve(sys.argv[2], reason))

        if action == "list":
            return print_result(list_quotes())

        if action == "latest":
            return print_result(latest_quote())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_quote_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "quote_generator_error",
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
