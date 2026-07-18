#!/usr/bin/env python3

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE_DIR / "ceo_memory"

FINANCE_FILE = MEMORY_DIR / "finance.json"
EXPENSES_FILE = MEMORY_DIR / "expenses.json"
APPROVALS_FILE = MEMORY_DIR / "spending_approvals.json"

DEFAULT_FINANCE_STATE = {
    "currency": "USD",
    "available_budget_usd": 0.0,
    "reserved_budget_usd": 0.0,
    "total_revenue_usd": 0.0,
    "total_expenses_usd": 0.0,
    "maximum_single_expense_usd": 5.0,
    "daily_spending_limit_usd": 10.0,
    "require_owner_approval_above_usd": 5.0,
    "updated_at": None,
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")

    with temporary.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    temporary.replace(path)


def initialize_finance_files() -> None:
    if not FINANCE_FILE.exists():
        state = dict(DEFAULT_FINANCE_STATE)
        state["updated_at"] = now()
        save_json(FINANCE_FILE, state)

    if not EXPENSES_FILE.exists():
        save_json(EXPENSES_FILE, [])

    if not APPROVALS_FILE.exists():
        save_json(APPROVALS_FILE, [])


def expenses_today(expenses: list[dict[str, Any]]) -> float:
    today = datetime.now(timezone.utc).date().isoformat()

    return sum(
        float(expense.get("amount_usd", 0))
        for expense in expenses
        if str(expense.get("created_at", "")).startswith(today)
        and expense.get("status") == "paid"
    )


def request_spending(task: dict[str, Any]) -> dict[str, Any]:
    initialize_finance_files()

    payload = task.get("payload", {})
    amount = float(payload.get("amount_usd", 0))
    purpose = str(payload.get("purpose", "")).strip()
    project_id = task.get("project_id")

    if amount <= 0:
        return {
            "success": False,
            "error": "amount_usd must be greater than zero",
        }

    if not purpose:
        return {
            "success": False,
            "error": "A spending purpose is required",
        }

    finance = load_json(FINANCE_FILE, dict(DEFAULT_FINANCE_STATE))
    expenses = load_json(EXPENSES_FILE, [])
    approvals = load_json(APPROVALS_FILE, [])

    available = float(finance.get("available_budget_usd", 0))
    reserved = float(finance.get("reserved_budget_usd", 0))
    spendable = max(available - reserved, 0)

    single_limit = float(
        finance.get("maximum_single_expense_usd", 5)
    )
    daily_limit = float(
        finance.get("daily_spending_limit_usd", 10)
    )
    owner_threshold = float(
        finance.get("require_owner_approval_above_usd", 5)
    )

    spent_today = expenses_today(expenses)
    reasons = []

    if amount > spendable:
        reasons.append(
            f"Requested ${amount:.2f}, but only "
            f"${spendable:.2f} is available"
        )

    if amount > single_limit:
        reasons.append(
            f"Amount exceeds the single-expense limit "
            f"of ${single_limit:.2f}"
        )

    if spent_today + amount > daily_limit:
        reasons.append(
            f"Amount would exceed the daily spending limit "
            f"of ${daily_limit:.2f}"
        )

    requires_owner = amount > owner_threshold

    if reasons:
        status = "rejected"
    elif requires_owner:
        status = "owner_approval_required"
    else:
        status = "approved"

    approval = {
        "id": f"approval-{uuid.uuid4().hex[:10]}",
        "task_id": task.get("id"),
        "project_id": project_id,
        "amount_usd": amount,
        "purpose": purpose,
        "status": status,
        "requires_owner_approval": requires_owner,
        "reasons": reasons,
        "created_at": now(),
        "approved_at": now() if status == "approved" else None,
        "paid_at": None,
    }

    approvals.append(approval)

    if status == "approved":
        finance["reserved_budget_usd"] = reserved + amount
        finance["updated_at"] = now()

    save_json(APPROVALS_FILE, approvals)
    save_json(FINANCE_FILE, finance)

    return {
        "success": status in {
            "approved",
            "owner_approval_required",
        },
        "status": status,
        "approval": approval,
        "finance_summary": {
            "available_budget_usd": available,
            "reserved_budget_usd": finance.get(
                "reserved_budget_usd",
                0,
            ),
            "spent_today_usd": spent_today,
        },
    }


def record_revenue(task: dict[str, Any]) -> dict[str, Any]:
    initialize_finance_files()

    payload = task.get("payload", {})
    amount = float(payload.get("amount_usd", 0))
    source = str(payload.get("source", "")).strip()

    if amount <= 0:
        return {
            "success": False,
            "error": "Revenue amount must be greater than zero",
        }

    if not source:
        return {
            "success": False,
            "error": "Revenue source is required",
        }

    finance = load_json(FINANCE_FILE, dict(DEFAULT_FINANCE_STATE))

    finance["available_budget_usd"] = (
        float(finance.get("available_budget_usd", 0)) + amount
    )
    finance["total_revenue_usd"] = (
        float(finance.get("total_revenue_usd", 0)) + amount
    )
    finance["updated_at"] = now()

    save_json(FINANCE_FILE, finance)

    return {
        "success": True,
        "status": "revenue_recorded",
        "amount_usd": amount,
        "source": source,
        "available_budget_usd": finance["available_budget_usd"],
    }


def record_expense(task: dict[str, Any]) -> dict[str, Any]:
    initialize_finance_files()

    payload = task.get("payload", {})
    approval_id = str(payload.get("approval_id", "")).strip()

    if not approval_id:
        return {
            "success": False,
            "error": "approval_id is required",
        }

    approvals = load_json(APPROVALS_FILE, [])
    expenses = load_json(EXPENSES_FILE, [])
    finance = load_json(FINANCE_FILE, dict(DEFAULT_FINANCE_STATE))

    approval = next(
        (
            item for item in approvals
            if item.get("id") == approval_id
        ),
        None,
    )

    if not approval:
        return {
            "success": False,
            "error": f"Approval not found: {approval_id}",
        }

    if approval.get("status") != "approved":
        return {
            "success": False,
            "error": (
                f"Approval status is {approval.get('status')}; "
                "expense cannot be recorded"
            ),
        }

    if approval.get("paid_at"):
        return {
            "success": False,
            "error": "This approval has already been used",
        }

    amount = float(approval["amount_usd"])

    expense = {
        "id": f"expense-{uuid.uuid4().hex[:10]}",
        "approval_id": approval_id,
        "project_id": approval.get("project_id"),
        "amount_usd": amount,
        "purpose": approval.get("purpose"),
        "status": "paid",
        "created_at": now(),
    }

    expenses.append(expense)
    approval["paid_at"] = now()
    approval["status"] = "paid"

    finance["available_budget_usd"] = max(
        float(finance.get("available_budget_usd", 0)) - amount,
        0,
    )
    finance["reserved_budget_usd"] = max(
        float(finance.get("reserved_budget_usd", 0)) - amount,
        0,
    )
    finance["total_expenses_usd"] = (
        float(finance.get("total_expenses_usd", 0)) + amount
    )
    finance["updated_at"] = now()

    save_json(EXPENSES_FILE, expenses)
    save_json(APPROVALS_FILE, approvals)
    save_json(FINANCE_FILE, finance)

    return {
        "success": True,
        "status": "expense_recorded",
        "expense": expense,
        "remaining_budget_usd": finance["available_budget_usd"],
    }


def financial_review() -> dict[str, Any]:
    initialize_finance_files()

    finance = load_json(FINANCE_FILE, dict(DEFAULT_FINANCE_STATE))
    expenses = load_json(EXPENSES_FILE, [])
    approvals = load_json(APPROVALS_FILE, [])

    pending_owner_approvals = [
        item
        for item in approvals
        if item.get("status") == "owner_approval_required"
    ]

    return {
        "success": True,
        "status": "financial_review_complete",
        "finance": finance,
        "expenses_today_usd": expenses_today(expenses),
        "pending_owner_approvals": pending_owner_approvals,
    }


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action == "request_spending":
        return request_spending(task)

    if action == "record_revenue":
        return record_revenue(task)

    if action == "record_expense":
        return record_expense(task)

    if action == "financial_review":
        return financial_review()

    return {
        "success": False,
        "error": f"Unsupported finance action: {action}",
    }


if __name__ == "__main__":
    print(json.dumps(financial_review(), indent=2))
