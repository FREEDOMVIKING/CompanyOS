#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
WORKSPACE="$ROOT/workspace"
BACKUP="$ROOT/backups/phase16_step6_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$WORKSPACE" "$BACKUP"

echo "============================================================"
echo " Phase 16 Step 6 - Accounting and Financial Operations"
echo "============================================================"

for file in \
  "$AGENTS/accounting_manager.py" \
  "$CTL/accountingctl" \
  "$MEMORY/accounting_config.json" \
  "$MEMORY/invoice_registry.json" \
  "$MEMORY/payment_registry.json" \
  "$MEMORY/expense_registry.json" \
  "$MEMORY/financial_kpis.json" \
  "$MEMORY/accounting_health.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/accounting_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_invoice_generation": false,
  "automatic_payment_collection": false,
  "automatic_bank_connection": false,
  "automatic_external_execution": false,
  "automatic_spending": false,
  "owner_approval_required_for_external_financial_actions": true,
  "default_currency": "USD",
  "default_payment_terms_days": 30
}
JSON

[ -f "$MEMORY/invoice_registry.json" ] || cat > "$MEMORY/invoice_registry.json" <<'JSON'
{
  "schema_version": 1,
  "invoices": [],
  "statistics": {
    "total": 0,
    "draft": 0,
    "issued": 0,
    "partially_paid": 0,
    "paid": 0,
    "void": 0
  },
  "last_updated_at": null
}
JSON

[ -f "$MEMORY/payment_registry.json" ] || cat > "$MEMORY/payment_registry.json" <<'JSON'
{
  "schema_version": 1,
  "payments": [],
  "statistics": {
    "total": 0,
    "recorded_amount": 0
  },
  "last_updated_at": null
}
JSON

[ -f "$MEMORY/expense_registry.json" ] || cat > "$MEMORY/expense_registry.json" <<'JSON'
{
  "schema_version": 1,
  "expenses": [],
  "statistics": {
    "total": 0,
    "recorded_amount": 0
  },
  "last_updated_at": null
}
JSON

cat > "$AGENTS/accounting_manager.py" <<'PY'
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
WORKSPACE = ROOT / "workspace" / "accounting"

CONFIG = MEMORY / "accounting_config.json"
PROJECTS = MEMORY / "project_registry.json"
INVOICES = MEMORY / "invoice_registry.json"
PAYMENTS = MEMORY / "payment_registry.json"
EXPENSES = MEMORY / "expense_registry.json"
KPIS = MEMORY / "financial_kpis.json"
HEALTH = MEMORY / "accounting_health.json"
AUDIT = MEMORY / "accounting_audit.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    tmp.replace(path)


def make_id(prefix: str, seed: str) -> str:
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


def latest_project() -> dict[str, Any] | None:
    projects = load_json(PROJECTS, {}).get("projects", [])
    return projects[-1] if projects else None


def update_invoice_stats(store: dict[str, Any]) -> None:
    records = store.get("invoices", [])
    statuses = ["draft", "issued", "partially_paid", "paid", "void"]
    stats = {"total": len(records)}
    for status in statuses:
        stats[status] = sum(
            1 for item in records
            if item.get("status") == status
        )
    store["statistics"] = stats
    store["last_updated_at"] = now()


def update_payment_stats(store: dict[str, Any]) -> None:
    records = store.get("payments", [])
    store["statistics"] = {
        "total": len(records),
        "recorded_amount": round(
            sum(float(item.get("amount") or 0) for item in records),
            2,
        ),
    }
    store["last_updated_at"] = now()


def update_expense_stats(store: dict[str, Any]) -> None:
    records = store.get("expenses", [])
    store["statistics"] = {
        "total": len(records),
        "recorded_amount": round(
            sum(float(item.get("amount") or 0) for item in records),
            2,
        ),
    }
    store["last_updated_at"] = now()


def invoice_total(invoice: dict[str, Any]) -> float:
    return round(
        sum(
            float(item.get("quantity") or 0)
            * float(item.get("unit_price") or 0)
            for item in invoice.get("line_items", [])
        ),
        2,
    )


def create_invoice_from_latest_project() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    project = latest_project()

    if not project:
        result = {
            "success": False,
            "status": "no_project_available",
        }
        audit("create_invoice", result)
        return result

    terms = int(config.get("default_payment_terms_days", 30))
    created = datetime.now(timezone.utc)
    due = (created + timedelta(days=terms)).date().isoformat()
    amount = float(project.get("amount") or 0)

    invoice = {
        "id": make_id("invoice", str(project.get("id"))),
        "project_id": project.get("id"),
        "customer_name": project.get("customer_name"),
        "project_name": project.get("project_name"),
        "currency": config.get("default_currency", "USD"),
        "status": "draft",
        "line_items": [
            {
                "description": project.get("project_name"),
                "quantity": 1,
                "unit_price": amount,
            }
        ],
        "subtotal": amount,
        "total": amount,
        "paid_amount": 0.0,
        "balance_due": amount,
        "issued_at": None,
        "due_date": due,
        "automatic_payment_collection": False,
        "automatic_bank_connection": False,
        "external_financial_execution_authorized": False,
        "created_at": created.isoformat(),
        "updated_at": created.isoformat(),
    }

    invoice["total"] = invoice_total(invoice)
    invoice["subtotal"] = invoice["total"]
    invoice["balance_due"] = invoice["total"]

    store = load_json(
        INVOICES,
        {
            "schema_version": 1,
            "invoices": [],
            "statistics": {},
        },
    )

    store.setdefault("invoices", []).append(invoice)
    update_invoice_stats(store)
    save_json(INVOICES, store)

    invoice_dir = WORKSPACE / invoice["id"]
    invoice_dir.mkdir(parents=True, exist_ok=True)

    (invoice_dir / "INVOICE.json").write_text(
        json.dumps(invoice, indent=2),
        encoding="utf-8",
    )

    (invoice_dir / "INVOICE.md").write_text(
        f"# Invoice\n\n"
        f"Invoice ID: {invoice['id']}\n\n"
        f"Customer: {invoice['customer_name']}\n\n"
        f"Project: {invoice['project_name']}\n\n"
        f"Total: ${invoice['total']:,.2f}\n\n"
        f"Due date: {invoice['due_date']}\n\n"
        f"Status: {invoice['status']}\n\n"
        "Payment collection is not automated.\n",
        encoding="utf-8",
    )

    result = {
        "success": True,
        "status": "invoice_created",
        "invoice": invoice,
        "workspace": str(invoice_dir),
        "automatic_payment_collection": False,
        "automatic_external_execution": False,
    }

    audit("create_invoice", result)
    return result


def issue_invoice(invoice_id: str) -> dict[str, Any]:
    store = load_json(INVOICES, {})

    for invoice in store.get("invoices", []):
        if invoice.get("id") != invoice_id:
            continue

        invoice["status"] = "issued"
        invoice["issued_at"] = now()
        invoice["updated_at"] = now()

        update_invoice_stats(store)
        save_json(INVOICES, store)

        result = {
            "success": True,
            "status": "invoice_marked_issued",
            "invoice_id": invoice_id,
            "customer_delivery_authorized": False,
        }

        audit("issue_invoice", result)
        return result

    result = {
        "success": False,
        "status": "invoice_not_found",
        "invoice_id": invoice_id,
    }
    audit("issue_invoice", result)
    return result


def record_payment(
    invoice_id: str,
    amount: float,
    method: str = "manual_record",
) -> dict[str, Any]:
    invoice_store = load_json(INVOICES, {})
    invoice = next(
        (
            item
            for item in invoice_store.get("invoices", [])
            if item.get("id") == invoice_id
        ),
        None,
    )

    if not invoice:
        result = {
            "success": False,
            "status": "invoice_not_found",
            "invoice_id": invoice_id,
        }
        audit("record_payment", result)
        return result

    payment = {
        "id": make_id("payment", invoice_id),
        "invoice_id": invoice_id,
        "amount": round(float(amount), 2),
        "method": method,
        "external_payment_processed": False,
        "recorded_at": now(),
    }

    payment_store = load_json(
        PAYMENTS,
        {
            "schema_version": 1,
            "payments": [],
            "statistics": {},
        },
    )

    payment_store.setdefault("payments", []).append(payment)
    update_payment_stats(payment_store)
    save_json(PAYMENTS, payment_store)

    invoice["paid_amount"] = round(
        float(invoice.get("paid_amount") or 0) + payment["amount"],
        2,
    )
    invoice["balance_due"] = round(
        max(float(invoice.get("total") or 0) - invoice["paid_amount"], 0),
        2,
    )

    if invoice["balance_due"] == 0:
        invoice["status"] = "paid"
    elif invoice["paid_amount"] > 0:
        invoice["status"] = "partially_paid"

    invoice["updated_at"] = now()
    update_invoice_stats(invoice_store)
    save_json(INVOICES, invoice_store)

    result = {
        "success": True,
        "status": "payment_recorded",
        "payment": payment,
        "invoice_balance_due": invoice["balance_due"],
        "external_payment_processed": False,
    }

    audit("record_payment", result)
    return result


def record_expense(
    description: str,
    amount: float,
    category: str = "general",
) -> dict[str, Any]:
    expense = {
        "id": make_id("expense", description),
        "description": description,
        "amount": round(float(amount), 2),
        "category": category,
        "external_spending_executed": False,
        "recorded_at": now(),
    }

    store = load_json(
        EXPENSES,
        {
            "schema_version": 1,
            "expenses": [],
            "statistics": {},
        },
    )

    store.setdefault("expenses", []).append(expense)
    update_expense_stats(store)
    save_json(EXPENSES, store)

    result = {
        "success": True,
        "status": "expense_recorded",
        "expense": expense,
        "external_spending_executed": False,
    }

    audit("record_expense", result)
    return result


def calculate_kpis() -> dict[str, Any]:
    invoices = load_json(INVOICES, {}).get("invoices", [])
    payments = load_json(PAYMENTS, {}).get("payments", [])
    expenses = load_json(EXPENSES, {}).get("expenses", [])

    invoiced = round(
        sum(float(item.get("total") or 0) for item in invoices),
        2,
    )
    received = round(
        sum(float(item.get("amount") or 0) for item in payments),
        2,
    )
    expenses_total = round(
        sum(float(item.get("amount") or 0) for item in expenses),
        2,
    )
    receivables = round(
        sum(float(item.get("balance_due") or 0) for item in invoices),
        2,
    )
    net_cash = round(received - expenses_total, 2)

    metrics = {
        "total_invoiced": invoiced,
        "cash_received": received,
        "accounts_receivable": receivables,
        "recorded_expenses": expenses_total,
        "net_cash_position": net_cash,
        "gross_margin_estimate": round(
            ((invoiced - expenses_total) / invoiced) * 100,
            2,
        ) if invoiced else 0.0,
        "invoice_count": len(invoices),
        "payment_count": len(payments),
        "expense_count": len(expenses),
        "external_payments_processed": 0,
        "external_spending_executed": 0,
        "calculated_at": now(),
    }

    save_json(
        KPIS,
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
        "status": "financial_kpis_calculated",
        "metrics": metrics,
    }

    audit("kpis", result)
    return result


def invoices() -> dict[str, Any]:
    store = load_json(INVOICES, {})
    result = {
        "success": True,
        "status": "invoice_list",
        "statistics": store.get("statistics", {}),
        "invoices": store.get("invoices", []),
    }
    audit("invoices", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    result = {
        "success": True,
        "status": "accounting_status",
        "enabled": config.get("enabled", False),
        "automatic_invoice_generation": config.get(
            "automatic_invoice_generation", False
        ),
        "automatic_payment_collection": config.get(
            "automatic_payment_collection", False
        ),
        "automatic_bank_connection": config.get(
            "automatic_bank_connection", False
        ),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_spending": config.get("automatic_spending", False),
        "invoice_statistics": load_json(INVOICES, {}).get("statistics", {}),
        "payment_statistics": load_json(PAYMENTS, {}).get("statistics", {}),
        "expense_statistics": load_json(EXPENSES, {}).get("statistics", {}),
        "financial_kpis": load_json(KPIS, {}).get("metrics", {}),
        "health": load_json(HEALTH, {}),
    }
    audit("status", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if action == "create-invoice-latest":
            return print_result(create_invoice_from_latest_project())

        if action == "issue":
            if len(sys.argv) < 3:
                raise ValueError("Invoice ID is required")
            return print_result(issue_invoice(sys.argv[2]))

        if action == "record-payment":
            if len(sys.argv) < 4:
                raise ValueError("Invoice ID and amount are required")
            method = sys.argv[4] if len(sys.argv) > 4 else "manual_record"
            return print_result(
                record_payment(
                    sys.argv[2],
                    float(sys.argv[3]),
                    method,
                )
            )

        if action == "record-expense":
            if len(sys.argv) < 4:
                raise ValueError("Description and amount are required")
            category = sys.argv[4] if len(sys.argv) > 4 else "general"
            return print_result(
                record_expense(
                    sys.argv[2],
                    float(sys.argv[3]),
                    category,
                )
            )

        if action == "kpis":
            return print_result(calculate_kpis())

        if action == "invoices":
            return print_result(invoices())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_accounting_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "accounting_error",
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

chmod +x "$AGENTS/accounting_manager.py"

cat > "$CTL/accountingctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "accounting_manager.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/accountingctl"

echo "[1/6] Compiling..."
python -m py_compile \
  "$AGENTS/accounting_manager.py" \
  "$CTL/accountingctl"

echo "[2/6] Creating draft invoice..."
INVOICE_OUTPUT="$(
  python "$CTL/accountingctl" create-invoice-latest
)"
echo "$INVOICE_OUTPUT"

INVOICE_ID="$(
  printf '%s' "$INVOICE_OUTPUT" \
  | python -c 'import json,sys; print(json.load(sys.stdin)["invoice"]["id"])'
)"

echo "[3/6] Recording safe internal payment and expense..."
python "$CTL/accountingctl" record-payment \
  "$INVOICE_ID" \
  "1000" \
  "manual_test_record"

python "$CTL/accountingctl" record-expense \
  "Sample material estimate" \
  "250" \
  "materials"

echo "[4/6] Calculating financial KPIs..."
python "$CTL/accountingctl" kpis

echo "[5/6] Checking accounting data..."
python "$CTL/accountingctl" invoices
python "$CTL/accountingctl" status

echo "[6/6] Verifying..."

python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "accounting_manager.py",
    root / "companyos" / "accountingctl",
    root / "ceo_memory" / "accounting_config.json",
    root / "ceo_memory" / "invoice_registry.json",
    root / "ceo_memory" / "payment_registry.json",
    root / "ceo_memory" / "expense_registry.json",
    root / "ceo_memory" / "financial_kpis.json",
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
        "automatic_invoice_generation",
        "automatic_payment_collection",
        "automatic_bank_connection",
        "automatic_external_execution",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

except Exception as exc:
    errors.append(f"Config error: {exc}")

try:
    invoices = json.loads(
        required[3].read_text(encoding="utf-8")
    ).get("invoices", [])

    payments = json.loads(
        required[4].read_text(encoding="utf-8")
    ).get("payments", [])

    expenses = json.loads(
        required[5].read_text(encoding="utf-8")
    ).get("expenses", [])

    metrics = json.loads(
        required[6].read_text(encoding="utf-8")
    ).get("metrics", {})

    if not invoices:
        errors.append("No invoice was created")

    if not payments:
        errors.append("No payment record was created")

    if not expenses:
        errors.append("No expense record was created")

    for field in [
        "total_invoiced",
        "cash_received",
        "accounts_receivable",
        "recorded_expenses",
        "net_cash_position",
    ]:
        if field not in metrics:
            errors.append(f"Missing KPI: {field}")

    if any(
        item.get("external_payment_processed") is not False
        for item in payments
    ):
        errors.append("External payment processing was enabled")

    if any(
        item.get("external_spending_executed") is not False
        for item in expenses
    ):
        errors.append("External spending was executed")

except Exception as exc:
    errors.append(f"Accounting memory error: {exc}")

print("--------------------------------------------")
print("Phase 16 Step 6 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 16 STEP 6 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/accountingctl create-invoice-latest"
echo "  python companyos/accountingctl issue INVOICE_ID"
echo "  python companyos/accountingctl record-payment INVOICE_ID AMOUNT METHOD"
echo "  python companyos/accountingctl record-expense \"DESCRIPTION\" AMOUNT CATEGORY"
echo "  python companyos/accountingctl kpis"
echo "  python companyos/accountingctl invoices"
echo "  python companyos/accountingctl status"
