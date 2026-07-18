#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
WORKSPACE="$ROOT/workspace"
BACKUP="$ROOT/backups/phase16_step2_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$WORKSPACE" "$BACKUP"

echo "============================================================"
echo " Phase 16 Step 2 - Quote and Proposal Generator"
echo "============================================================"

for file in \
  "$AGENTS/quote_proposal_generator.py" \
  "$CTL/quotectl" \
  "$MEMORY/quote_config.json" \
  "$MEMORY/quote_registry.json" \
  "$MEMORY/quote_health.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/quote_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_quote_generation": false,
  "automatic_customer_delivery": false,
  "automatic_email": false,
  "automatic_sms": false,
  "automatic_external_execution": false,
  "automatic_spending": false,
  "owner_approval_required_before_delivery": true,
  "default_currency": "USD",
  "default_valid_days": 30
}
JSON

if [ ! -f "$MEMORY/quote_registry.json" ]; then
cat > "$MEMORY/quote_registry.json" <<'JSON'
{
  "schema_version": 1,
  "quotes": [],
  "statistics": {
    "total": 0,
    "draft": 0,
    "approved": 0,
    "sent": 0,
    "accepted": 0,
    "rejected": 0
  },
  "last_updated_at": null
}
JSON
fi

cat > "$AGENTS/quote_proposal_generator.py" <<'PY'
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
PY

chmod +x "$AGENTS/quote_proposal_generator.py"

cat > "$CTL/quotectl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "quote_proposal_generator.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/quotectl"

echo "[1/5] Compiling..."
python -m py_compile \
  "$AGENTS/quote_proposal_generator.py" \
  "$CTL/quotectl"

echo "[2/5] Generating quote from latest lead..."
python "$CTL/quotectl" generate-latest

echo "[3/5] Checking quote data..."
python "$CTL/quotectl" latest
python "$CTL/quotectl" list
python "$CTL/quotectl" status

echo "[4/5] Verifying..."

python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "quote_proposal_generator.py",
    root / "companyos" / "quotectl",
    root / "ceo_memory" / "quote_config.json",
    root / "ceo_memory" / "quote_registry.json",
]

for path in required:
    if not path.exists():
        errors.append(f"Missing: {path}")

for path in required[:2]:
    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        errors.append(f"Compile error: {exc}")

try:
    config = json.loads(required[2].read_text(encoding="utf-8"))

    for field in [
        "automatic_quote_generation",
        "automatic_customer_delivery",
        "automatic_email",
        "automatic_sms",
        "automatic_external_execution",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

except Exception as exc:
    errors.append(f"Config error: {exc}")

try:
    quotes = json.loads(
        required[3].read_text(encoding="utf-8")
    ).get("quotes", [])

    if not quotes:
        errors.append("No quote was generated")
    else:
        latest = quotes[-1]

        if latest.get("status") != "draft":
            errors.append("Latest quote should remain draft")

        if latest.get("owner_approved") is not False:
            errors.append("Quote was approved automatically")

        markdown = Path(str(latest.get("markdown_path", "")))
        if not markdown.exists():
            errors.append("Quote document is missing")

except Exception as exc:
    errors.append(f"Quote registry error: {exc}")

print("--------------------------------------------")
print("Phase 16 Step 2 verification")
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
echo " PHASE 16 STEP 2 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/quotectl generate-latest"
echo "  python companyos/quotectl generate LEAD_ID \"SCOPE\""
echo "  python companyos/quotectl approve QUOTE_ID \"Owner approved\""
echo "  python companyos/quotectl latest"
echo "  python companyos/quotectl list"
echo "  python companyos/quotectl status"
