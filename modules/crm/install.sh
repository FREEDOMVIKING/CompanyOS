#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
AGENTS_DIR="$ROOT_DIR/agents"
MEMORY_DIR="$ROOT_DIR/ceo_memory"
MANIFEST_FILE="$ROOT_DIR/companyos/manifest.json"

mkdir -p "$AGENTS_DIR" "$MEMORY_DIR/crm_reports"
touch "$AGENTS_DIR/__init__.py"

echo
echo "[1/6] Creating CRM agent..."

cat > "$AGENTS_DIR/crm_agent.py" <<'PYTHON'
#!/usr/bin/env python3

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
MEMORY_DIR = BASE_DIR / "ceo_memory"

LEADS_FILE = MEMORY_DIR / "crm_leads.json"
ACTIVITY_FILE = MEMORY_DIR / "crm_activity.json"
PIPELINE_FILE = MEMORY_DIR / "crm_pipeline.json"
CUSTOMERS_FILE = MEMORY_DIR / "crm_customers.json"
SUMMARY_FILE = MEMORY_DIR / "crm_summary.json"
REPORT_DIR = MEMORY_DIR / "crm_reports"

VALID_STAGES = {
    "new",
    "researching",
    "contacted",
    "interested",
    "qualified",
    "proposal",
    "negotiation",
    "won",
    "lost",
}

SAFE_ID = re.compile(r"^[a-zA-Z0-9_-]+$")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def normalize_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def find_record(
    records: list[dict[str, Any]],
    record_id: str,
) -> dict[str, Any] | None:
    return next(
        (
            item
            for item in records
            if str(item.get("id", "")) == record_id
        ),
        None,
    )


def validate_stage(stage: str) -> str:
    stage = stage.strip().lower()

    if stage not in VALID_STAGES:
        raise ValueError(
            "Invalid CRM stage. Allowed stages: "
            + ", ".join(sorted(VALID_STAGES))
        )

    return stage


def create_lead(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    name = str(payload.get("name", "")).strip()
    organization = str(
        payload.get("organization", "")
    ).strip()
    email = str(payload.get("email", "")).strip()
    phone = str(payload.get("phone", "")).strip()
    source = str(payload.get("source", "manual")).strip()
    project_id = str(
        payload.get(
            "project_id",
            task.get("project_id", ""),
        )
    ).strip()
    venture_id = str(payload.get("venture_id", "")).strip()

    if not name and not organization:
        return {
            "success": False,
            "error": "Lead name or organization is required",
        }

    leads = normalize_list(load_json(LEADS_FILE, []))

    duplicate = next(
        (
            lead
            for lead in leads
            if email
            and str(lead.get("email", "")).lower()
            == email.lower()
        ),
        None,
    )

    if duplicate:
        return {
            "success": False,
            "error": "A lead with this email already exists",
            "lead_id": duplicate.get("id"),
        }

    lead = {
        "id": f"lead-{uuid.uuid4().hex[:10]}",
        "name": name,
        "organization": organization,
        "email": email,
        "phone": phone,
        "source": source,
        "project_id": project_id or None,
        "venture_id": venture_id or None,
        "stage": "new",
        "status": "active",
        "estimated_value_usd": float(
            payload.get("estimated_value_usd", 0) or 0
        ),
        "probability": 0.05,
        "next_follow_up_at": payload.get(
            "next_follow_up_at"
        ),
        "notes": payload.get("notes", ""),
        "created_at": now(),
        "updated_at": now(),
    }

    leads.append(lead)
    save_json(LEADS_FILE, leads)

    record_activity(
        lead_id=lead["id"],
        activity_type="lead_created",
        note=f"Lead created from source: {source}",
    )

    refresh_pipeline()

    return {
        "success": True,
        "status": "lead_created",
        "lead": lead,
    }


def record_activity(
    lead_id: str,
    activity_type: str,
    note: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    activity = normalize_list(load_json(ACTIVITY_FILE, []))

    entry = {
        "id": f"activity-{uuid.uuid4().hex[:10]}",
        "lead_id": lead_id,
        "type": activity_type,
        "note": note,
        "metadata": metadata or {},
        "created_at": now(),
    }

    activity.append(entry)
    save_json(ACTIVITY_FILE, activity[-5000:])

    return entry


def update_lead_stage(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    lead_id = str(payload.get("lead_id", "")).strip()
    stage = validate_stage(
        str(payload.get("stage", ""))
    )

    if not lead_id:
        return {
            "success": False,
            "error": "lead_id is required",
        }

    leads = normalize_list(load_json(LEADS_FILE, []))
    lead = find_record(leads, lead_id)

    if lead is None:
        return {
            "success": False,
            "error": f"Lead not found: {lead_id}",
        }

    previous_stage = lead.get("stage")
    lead["stage"] = stage
    lead["updated_at"] = now()

    probability_map = {
        "new": 0.05,
        "researching": 0.10,
        "contacted": 0.20,
        "interested": 0.35,
        "qualified": 0.50,
        "proposal": 0.65,
        "negotiation": 0.80,
        "won": 1.0,
        "lost": 0.0,
    }

    lead["probability"] = probability_map[stage]

    if stage == "won":
        lead["status"] = "converted"
        create_customer_from_lead(lead)

    elif stage == "lost":
        lead["status"] = "closed"

    save_json(LEADS_FILE, leads)

    activity = record_activity(
        lead_id=lead_id,
        activity_type="stage_changed",
        note=f"Stage changed from {previous_stage} to {stage}",
        metadata={
            "previous_stage": previous_stage,
            "new_stage": stage,
        },
    )

    refresh_pipeline()

    return {
        "success": True,
        "status": "lead_stage_updated",
        "lead": lead,
        "activity": activity,
    }


def add_activity(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    lead_id = str(payload.get("lead_id", "")).strip()
    activity_type = str(
        payload.get("type", "note")
    ).strip()
    note = str(payload.get("note", "")).strip()

    if not lead_id:
        return {
            "success": False,
            "error": "lead_id is required",
        }

    leads = normalize_list(load_json(LEADS_FILE, []))

    if find_record(leads, lead_id) is None:
        return {
            "success": False,
            "error": f"Lead not found: {lead_id}",
        }

    entry = record_activity(
        lead_id=lead_id,
        activity_type=activity_type,
        note=note,
        metadata=payload.get("metadata", {}),
    )

    return {
        "success": True,
        "status": "crm_activity_recorded",
        "activity": entry,
    }


def create_customer_from_lead(
    lead: dict[str, Any],
) -> dict[str, Any]:
    customers = normalize_list(load_json(CUSTOMERS_FILE, []))

    existing = next(
        (
            customer
            for customer in customers
            if customer.get("lead_id") == lead.get("id")
        ),
        None,
    )

    if existing:
        return existing

    customer = {
        "id": f"customer-{uuid.uuid4().hex[:10]}",
        "lead_id": lead.get("id"),
        "name": lead.get("name"),
        "organization": lead.get("organization"),
        "email": lead.get("email"),
        "phone": lead.get("phone"),
        "project_id": lead.get("project_id"),
        "venture_id": lead.get("venture_id"),
        "lifetime_value_usd": float(
            lead.get("estimated_value_usd", 0) or 0
        ),
        "status": "active",
        "created_at": now(),
        "updated_at": now(),
    }

    customers.append(customer)
    save_json(CUSTOMERS_FILE, customers)

    return customer


def refresh_pipeline() -> dict[str, Any]:
    leads = normalize_list(load_json(LEADS_FILE, []))

    stages = {
        stage: []
        for stage in sorted(VALID_STAGES)
    }

    total_estimated_value = 0.0
    weighted_pipeline_value = 0.0

    for lead in leads:
        stage = str(lead.get("stage", "new"))

        if stage not in stages:
            stage = "new"

        stages[stage].append(lead.get("id"))

        value = float(
            lead.get("estimated_value_usd", 0) or 0
        )
        probability = float(
            lead.get("probability", 0) or 0
        )

        total_estimated_value += value
        weighted_pipeline_value += value * probability

    summary = {
        "success": True,
        "status": "pipeline_refreshed",
        "updated_at": now(),
        "total_leads": len(leads),
        "active_leads": len([
            lead
            for lead in leads
            if lead.get("status") == "active"
        ]),
        "won_leads": len(stages["won"]),
        "lost_leads": len(stages["lost"]),
        "total_estimated_value_usd": round(
            total_estimated_value,
            2,
        ),
        "weighted_pipeline_value_usd": round(
            weighted_pipeline_value,
            2,
        ),
        "stage_counts": {
            stage: len(ids)
            for stage, ids in stages.items()
        },
        "stages": stages,
    }

    save_json(PIPELINE_FILE, summary)
    save_json(SUMMARY_FILE, summary)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_file = REPORT_DIR / (
        "crm_report_"
        + datetime.now(timezone.utc).strftime(
            "%Y%m%d_%H%M%S"
        )
        + ".json"
    )

    save_json(report_file, summary)

    return summary


def list_leads(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    leads = normalize_list(load_json(LEADS_FILE, []))
    stage_filter = str(
        payload.get("stage", "")
    ).strip().lower()
    project_filter = str(
        payload.get("project_id", "")
    ).strip()

    if stage_filter:
        leads = [
            lead
            for lead in leads
            if str(lead.get("stage", "")).lower()
            == stage_filter
        ]

    if project_filter:
        leads = [
            lead
            for lead in leads
            if str(lead.get("project_id", ""))
            == project_filter
        ]

    return {
        "success": True,
        "status": "leads_listed",
        "count": len(leads),
        "leads": leads,
    }


def list_customers() -> dict[str, Any]:
    customers = normalize_list(
        load_json(CUSTOMERS_FILE, [])
    )

    return {
        "success": True,
        "status": "customers_listed",
        "count": len(customers),
        "customers": customers,
    }


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action == "create_lead":
        return create_lead(task)

    if action == "update_lead_stage":
        return update_lead_stage(task)

    if action == "add_crm_activity":
        return add_activity(task)

    if action == "list_leads":
        return list_leads(task)

    if action == "list_customers":
        return list_customers()

    if action in {"pipeline_summary", "refresh_pipeline"}:
        return refresh_pipeline()

    return {
        "success": False,
        "error": f"Unsupported CRM action: {action}",
    }


if __name__ == "__main__":
    print(json.dumps(refresh_pipeline(), indent=2))
PYTHON

chmod +x "$AGENTS_DIR/crm_agent.py"

echo
echo "[2/6] Initializing CRM memory..."

for FILE in \
    crm_leads.json \
    crm_activity.json \
    crm_customers.json
do
    [ -f "$MEMORY_DIR/$FILE" ] || \
        printf '[]\n' > "$MEMORY_DIR/$FILE"
done

for FILE in \
    crm_pipeline.json \
    crm_summary.json
do
    [ -f "$MEMORY_DIR/$FILE" ] || \
        printf '{}\n' > "$MEMORY_DIR/$FILE"
done

echo
echo "[3/6] Creating CRM command utility..."

cat > "$ROOT_DIR/companyos/crmctl" <<'PYTHON'
#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from agents.crm_agent import run_task


def output(data) -> None:
    print(json.dumps(data, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CompanyOS CRM"
    )

    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    commands.add_parser("pipeline")
    commands.add_parser("list")
    commands.add_parser("customers")

    create_parser = commands.add_parser("create")
    create_parser.add_argument("--name", default="")
    create_parser.add_argument("--organization", default="")
    create_parser.add_argument("--email", default="")
    create_parser.add_argument("--phone", default="")
    create_parser.add_argument("--source", default="manual")
    create_parser.add_argument("--project-id", default="")
    create_parser.add_argument("--venture-id", default="")
    create_parser.add_argument(
        "--value",
        type=float,
        default=0.0,
    )

    stage_parser = commands.add_parser("stage")
    stage_parser.add_argument("lead_id")
    stage_parser.add_argument("stage")

    note_parser = commands.add_parser("note")
    note_parser.add_argument("lead_id")
    note_parser.add_argument("note")

    args = parser.parse_args()

    if args.command == "pipeline":
        result = run_task({
            "action": "pipeline_summary",
        })

    elif args.command == "list":
        result = run_task({
            "action": "list_leads",
            "payload": {},
        })

    elif args.command == "customers":
        result = run_task({
            "action": "list_customers",
        })

    elif args.command == "create":
        result = run_task({
            "action": "create_lead",
            "payload": {
                "name": args.name,
                "organization": args.organization,
                "email": args.email,
                "phone": args.phone,
                "source": args.source,
                "project_id": args.project_id,
                "venture_id": args.venture_id,
                "estimated_value_usd": args.value,
            },
        })

    elif args.command == "stage":
        result = run_task({
            "action": "update_lead_stage",
            "payload": {
                "lead_id": args.lead_id,
                "stage": args.stage,
            },
        })

    else:
        result = run_task({
            "action": "add_crm_activity",
            "payload": {
                "lead_id": args.lead_id,
                "type": "note",
                "note": args.note,
            },
        })

    output(result)

    if result.get("success") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
PYTHON

chmod +x "$ROOT_DIR/companyos/crmctl"

echo
echo "[4/6] Updating CompanyOS manifest..."

python - "$MANIFEST_FILE" <<'PYTHON'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))

modules = data.setdefault("modules", {})
crm = modules.setdefault("crm", {})

crm.update({
    "installed": True,
    "enabled": True,
    "version": "1.0.0",
    "agent": "agents/crm_agent.py",
    "commands": [
        "pipeline",
        "list",
        "customers",
        "create",
        "stage",
        "note"
    ]
})

path.write_text(
    json.dumps(data, indent=2),
    encoding="utf-8",
)

print("CRM manifest entry updated.")
PYTHON

echo
echo "[5/6] Compiling and testing CRM..."

python -m py_compile \
    "$AGENTS_DIR/crm_agent.py" \
    "$ROOT_DIR/companyos/crmctl"

python "$ROOT_DIR/companyos/crmctl" pipeline

echo
echo "[6/6] Running CompanyOS verification..."

bash "$ROOT_DIR/companyos/verify.sh"

echo
echo "============================================================"
echo " SALES PIPELINE AND CRM INSTALLED SUCCESSFULLY"
echo "============================================================"
echo
echo "Create a test lead:"
echo
echo "  python companyos/crmctl create \\"
echo '    --name "Sample Customer" \'
echo '    --organization "Sample Business" \'
echo '    --email "sample@example.com" \'
echo '    --source "manual test" \'
echo '    --value 100'
echo
echo "View the sales pipeline:"
echo
echo "  python companyos/crmctl pipeline"
