#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/companyos"
AGENTS="$ROOT/agents"
CTL="$ROOT/companyos"
MEMORY="$ROOT/ceo_memory"
WORKSPACE="$ROOT/workspace"
BACKUP="$ROOT/backups/phase16_step4_$(date +%Y%m%d_%H%M%S)"

cd "$ROOT"
mkdir -p "$AGENTS" "$CTL" "$MEMORY" "$WORKSPACE" "$BACKUP"

echo "============================================================"
echo " Phase 16 Step 4 - Customer Portal and Project Tracker"
echo "============================================================"

for file in \
  "$AGENTS/project_tracker.py" \
  "$CTL/projectctl" \
  "$MEMORY/project_tracker_config.json" \
  "$MEMORY/project_registry.json" \
  "$MEMORY/project_milestones.json" \
  "$MEMORY/project_documents.json" \
  "$MEMORY/project_tracker_health.json"
do
  if [ -f "$file" ]; then
    cp -a "$file" "$BACKUP/"
  fi
done

cat > "$MEMORY/project_tracker_config.json" <<'JSON'
{
  "enabled": true,
  "automatic_customer_portal_publication": false,
  "automatic_customer_notifications": false,
  "automatic_external_file_sharing": false,
  "automatic_external_execution": false,
  "automatic_spending": false,
  "owner_approval_required_for_customer_access": true,
  "default_project_status": "planning",
  "project_statuses": [
    "planning",
    "scheduled",
    "in_progress",
    "waiting",
    "completed",
    "cancelled"
  ]
}
JSON

[ -f "$MEMORY/project_registry.json" ] || cat > "$MEMORY/project_registry.json" <<'JSON'
{
  "schema_version": 1,
  "projects": [],
  "statistics": {
    "total": 0,
    "planning": 0,
    "scheduled": 0,
    "in_progress": 0,
    "waiting": 0,
    "completed": 0,
    "cancelled": 0
  },
  "last_updated_at": null
}
JSON

[ -f "$MEMORY/project_milestones.json" ] || cat > "$MEMORY/project_milestones.json" <<'JSON'
{
  "schema_version": 1,
  "milestones": [],
  "statistics": {
    "total": 0,
    "pending": 0,
    "in_progress": 0,
    "completed": 0
  },
  "last_updated_at": null
}
JSON

[ -f "$MEMORY/project_documents.json" ] || cat > "$MEMORY/project_documents.json" <<'JSON'
{
  "schema_version": 1,
  "documents": [],
  "last_updated_at": null
}
JSON

cat > "$AGENTS/project_tracker.py" <<'PY'
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
WORKSPACE = ROOT / "workspace" / "projects"

CONFIG = MEMORY / "project_tracker_config.json"
PROJECTS = MEMORY / "project_registry.json"
MILESTONES = MEMORY / "project_milestones.json"
DOCUMENTS = MEMORY / "project_documents.json"
QUOTES = MEMORY / "quote_registry.json"
HEALTH = MEMORY / "project_tracker_health.json"
AUDIT = MEMORY / "project_tracker_audit.json"


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


def safe_name(value: str) -> str:
    text = "".join(
        c.lower() if c.isalnum() else "_"
        for c in value
    )
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_") or "project"


def latest_quote() -> dict[str, Any] | None:
    quotes = load_json(QUOTES, {}).get("quotes", [])
    return quotes[-1] if quotes else None


def update_project_stats(store: dict[str, Any]) -> None:
    records = store.get("projects", [])
    statuses = [
        "planning",
        "scheduled",
        "in_progress",
        "waiting",
        "completed",
        "cancelled",
    ]

    stats = {"total": len(records)}
    for status in statuses:
        stats[status] = sum(
            1 for item in records
            if item.get("status") == status
        )

    store["statistics"] = stats
    store["last_updated_at"] = now()


def update_milestone_stats(store: dict[str, Any]) -> None:
    records = store.get("milestones", [])
    statuses = ["pending", "in_progress", "completed"]

    stats = {"total": len(records)}
    for status in statuses:
        stats[status] = sum(
            1 for item in records
            if item.get("status") == status
        )

    store["statistics"] = stats
    store["last_updated_at"] = now()


def project_progress(project_id: str) -> int:
    records = [
        item
        for item in load_json(MILESTONES, {}).get("milestones", [])
        if item.get("project_id") == project_id
    ]

    if not records:
        return 0

    completed = sum(
        1 for item in records
        if item.get("status") == "completed"
    )

    return round((completed / len(records)) * 100)


def project_health(project: dict[str, Any]) -> str:
    progress = int(project.get("progress_percent", 0))
    status = project.get("status")

    if status == "completed":
        return "healthy"

    if status == "cancelled":
        return "closed"

    if progress >= 75:
        return "healthy"

    if progress >= 30:
        return "stable"

    return "needs_review"


def create_project(
    customer_name: str,
    project_name: str,
    amount: float | None = None,
    source_quote_id: str | None = None,
) -> dict[str, Any]:
    if not customer_name.strip() or not project_name.strip():
        result = {
            "success": False,
            "status": "customer_and_project_required",
        }
        audit("create_project", result)
        return result

    project_id = make_id(
        "project",
        f"{customer_name}:{project_name}",
    )

    project_dir = WORKSPACE / safe_name(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    project = {
        "id": project_id,
        "customer_name": customer_name.strip(),
        "project_name": project_name.strip(),
        "amount": amount,
        "source_quote_id": source_quote_id,
        "status": "planning",
        "progress_percent": 0,
        "health": "needs_review",
        "customer_portal_enabled": False,
        "external_file_sharing_enabled": False,
        "customer_notifications_enabled": False,
        "workspace": str(project_dir),
        "created_at": now(),
        "updated_at": now(),
    }

    store = load_json(
        PROJECTS,
        {
            "schema_version": 1,
            "projects": [],
            "statistics": {},
        },
    )

    store.setdefault("projects", []).append(project)
    update_project_stats(store)
    save_json(PROJECTS, store)

    (project_dir / "PROJECT.json").write_text(
        json.dumps(project, indent=2),
        encoding="utf-8",
    )

    result = {
        "success": True,
        "status": "project_created",
        "project": project,
        "automatic_customer_portal_publication": False,
        "automatic_customer_notifications": False,
    }

    audit("create_project", result)
    return result


def create_from_latest_quote() -> dict[str, Any]:
    quote = latest_quote()

    if not quote:
        result = {
            "success": False,
            "status": "no_quote_available",
        }
        audit("create_from_latest_quote", result)
        return result

    return create_project(
        str(quote.get("customer_name") or "Unknown Customer"),
        str(quote.get("project_name") or "Untitled Project"),
        float(quote.get("amount") or 0),
        str(quote.get("id")),
    )


def add_milestone(
    project_id: str,
    title: str,
    description: str | None = None,
) -> dict[str, Any]:
    projects = load_json(PROJECTS, {}).get("projects", [])

    if not any(item.get("id") == project_id for item in projects):
        result = {
            "success": False,
            "status": "project_not_found",
            "project_id": project_id,
        }
        audit("add_milestone", result)
        return result

    store = load_json(
        MILESTONES,
        {
            "schema_version": 1,
            "milestones": [],
            "statistics": {},
        },
    )

    milestone = {
        "id": make_id("milestone", f"{project_id}:{title}"),
        "project_id": project_id,
        "title": title.strip(),
        "description": description,
        "status": "pending",
        "created_at": now(),
        "updated_at": now(),
    }

    store.setdefault("milestones", []).append(milestone)
    update_milestone_stats(store)
    save_json(MILESTONES, store)

    refresh_project(project_id)

    result = {
        "success": True,
        "status": "milestone_created",
        "milestone": milestone,
    }

    audit("add_milestone", result)
    return result


def set_milestone_status(
    milestone_id: str,
    status: str,
) -> dict[str, Any]:
    allowed = {"pending", "in_progress", "completed"}

    if status not in allowed:
        result = {
            "success": False,
            "status": "invalid_milestone_status",
            "allowed_statuses": sorted(allowed),
        }
        audit("set_milestone_status", result)
        return result

    store = load_json(MILESTONES, {})

    for milestone in store.get("milestones", []):
        if milestone.get("id") != milestone_id:
            continue

        milestone["status"] = status
        milestone["updated_at"] = now()

        if status == "completed":
            milestone["completed_at"] = now()

        update_milestone_stats(store)
        save_json(MILESTONES, store)

        refresh_project(str(milestone.get("project_id")))

        result = {
            "success": True,
            "status": "milestone_status_updated",
            "milestone_id": milestone_id,
            "new_status": status,
        }

        audit("set_milestone_status", result)
        return result

    result = {
        "success": False,
        "status": "milestone_not_found",
        "milestone_id": milestone_id,
    }

    audit("set_milestone_status", result)
    return result


def refresh_project(project_id: str) -> None:
    store = load_json(PROJECTS, {})

    for project in store.get("projects", []):
        if project.get("id") != project_id:
            continue

        project["progress_percent"] = project_progress(project_id)
        project["health"] = project_health(project)
        project["updated_at"] = now()

        if project["progress_percent"] == 100:
            project["status"] = "completed"
            project["health"] = "healthy"

    update_project_stats(store)
    save_json(PROJECTS, store)


def add_document(
    project_id: str,
    name: str,
    path: str,
    document_type: str = "general",
) -> dict[str, Any]:
    project = next(
        (
            item
            for item in load_json(PROJECTS, {}).get("projects", [])
            if item.get("id") == project_id
        ),
        None,
    )

    if not project:
        result = {
            "success": False,
            "status": "project_not_found",
            "project_id": project_id,
        }
        audit("add_document", result)
        return result

    document_path = Path(path).expanduser()

    record = {
        "id": make_id("document", f"{project_id}:{name}"),
        "project_id": project_id,
        "name": name,
        "document_type": document_type,
        "path": str(document_path),
        "exists": document_path.exists(),
        "external_file_sharing_authorized": False,
        "created_at": now(),
    }

    store = load_json(
        DOCUMENTS,
        {
            "schema_version": 1,
            "documents": [],
            "last_updated_at": None,
        },
    )

    store.setdefault("documents", []).append(record)
    store["last_updated_at"] = now()
    save_json(DOCUMENTS, store)

    result = {
        "success": True,
        "status": "project_document_registered",
        "document": record,
        "automatic_external_file_sharing": False,
    }

    audit("add_document", result)
    return result


def list_projects() -> dict[str, Any]:
    store = load_json(PROJECTS, {})
    result = {
        "success": True,
        "status": "project_list",
        "count": len(store.get("projects", [])),
        "statistics": store.get("statistics", {}),
        "projects": store.get("projects", []),
    }
    audit("projects", result)
    return result


def list_milestones() -> dict[str, Any]:
    store = load_json(MILESTONES, {})
    result = {
        "success": True,
        "status": "milestone_list",
        "count": len(store.get("milestones", [])),
        "statistics": store.get("statistics", {}),
        "milestones": store.get("milestones", []),
    }
    audit("milestones", result)
    return result


def status() -> dict[str, Any]:
    config = load_json(CONFIG, {})
    projects = load_json(PROJECTS, {})
    milestones = load_json(MILESTONES, {})
    health = load_json(HEALTH, {})

    result = {
        "success": True,
        "status": "project_tracker_status",
        "enabled": config.get("enabled", False),
        "automatic_customer_portal_publication": config.get(
            "automatic_customer_portal_publication", False
        ),
        "automatic_customer_notifications": config.get(
            "automatic_customer_notifications", False
        ),
        "automatic_external_file_sharing": config.get(
            "automatic_external_file_sharing", False
        ),
        "automatic_external_execution": config.get(
            "automatic_external_execution", False
        ),
        "automatic_spending": config.get(
            "automatic_spending", False
        ),
        "project_statistics": projects.get("statistics", {}),
        "milestone_statistics": milestones.get("statistics", {}),
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
        if action == "create":
            if len(sys.argv) < 4:
                raise ValueError(
                    "Customer name and project name are required"
                )

            amount = (
                float(sys.argv[4])
                if len(sys.argv) > 4
                else None
            )

            return print_result(
                create_project(
                    sys.argv[2],
                    sys.argv[3],
                    amount,
                )
            )

        if action == "create-from-latest-quote":
            return print_result(create_from_latest_quote())

        if action == "add-milestone":
            if len(sys.argv) < 4:
                raise ValueError(
                    "Project ID and milestone title are required"
                )

            description = " ".join(sys.argv[4:]).strip() or None

            return print_result(
                add_milestone(
                    sys.argv[2],
                    sys.argv[3],
                    description,
                )
            )

        if action == "set-milestone":
            if len(sys.argv) < 4:
                raise ValueError(
                    "Milestone ID and status are required"
                )

            return print_result(
                set_milestone_status(
                    sys.argv[2],
                    sys.argv[3],
                )
            )

        if action == "add-document":
            if len(sys.argv) < 5:
                raise ValueError(
                    "Project ID, document name and path are required"
                )

            document_type = (
                sys.argv[5]
                if len(sys.argv) > 5
                else "general"
            )

            return print_result(
                add_document(
                    sys.argv[2],
                    sys.argv[3],
                    sys.argv[4],
                    document_type,
                )
            )

        if action == "projects":
            return print_result(list_projects())

        if action == "milestones":
            return print_result(list_milestones())

        if action == "status":
            return print_result(status())

        return print_result({
            "success": False,
            "status": "unknown_project_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "project_tracker_error",
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

chmod +x "$AGENTS/project_tracker.py"

cat > "$CTL/projectctl" <<'PY'
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

root = Path.home() / "companyos"
agent = root / "agents" / "project_tracker.py"

raise SystemExit(
    subprocess.call(
        [sys.executable, str(agent), *sys.argv[1:]],
        cwd=root,
    )
)
PY

chmod +x "$CTL/projectctl"

echo "[1/6] Compiling..."
python -m py_compile \
  "$AGENTS/project_tracker.py" \
  "$CTL/projectctl"

echo "[2/6] Creating project from latest quote..."
PROJECT_OUTPUT="$(
  python "$CTL/projectctl" create-from-latest-quote
)"
echo "$PROJECT_OUTPUT"

PROJECT_ID="$(
  printf '%s' "$PROJECT_OUTPUT" \
  | python -c 'import json,sys; print(json.load(sys.stdin)["project"]["id"])'
)"

echo "[3/6] Adding internal milestones..."
python "$CTL/projectctl" add-milestone \
  "$PROJECT_ID" \
  "Confirm scope" \
  "Review the approved project scope."

python "$CTL/projectctl" add-milestone \
  "$PROJECT_ID" \
  "Schedule work" \
  "Create an internal work schedule."

python "$CTL/projectctl" add-milestone \
  "$PROJECT_ID" \
  "Complete project" \
  "Finish work and complete internal review."

echo "[4/6] Registering project document..."
python "$CTL/projectctl" add-document \
  "$PROJECT_ID" \
  "Project record" \
  "$MEMORY/project_registry.json" \
  "internal_record"

echo "[5/6] Checking project tracker..."
python "$CTL/projectctl" projects
python "$CTL/projectctl" milestones
python "$CTL/projectctl" status

echo "[6/6] Verifying..."

python - <<'PY'
import json
import py_compile
from pathlib import Path

root = Path.home() / "companyos"
errors = []

required = [
    root / "agents" / "project_tracker.py",
    root / "companyos" / "projectctl",
    root / "ceo_memory" / "project_tracker_config.json",
    root / "ceo_memory" / "project_registry.json",
    root / "ceo_memory" / "project_milestones.json",
    root / "ceo_memory" / "project_documents.json",
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
        "automatic_customer_portal_publication",
        "automatic_customer_notifications",
        "automatic_external_file_sharing",
        "automatic_external_execution",
        "automatic_spending",
    ]:
        if config.get(field) is not False:
            errors.append(f"{field} must remain disabled")

except Exception as exc:
    errors.append(f"Config error: {exc}")

try:
    projects = json.loads(
        required[3].read_text(encoding="utf-8")
    ).get("projects", [])

    milestones = json.loads(
        required[4].read_text(encoding="utf-8")
    ).get("milestones", [])

    documents = json.loads(
        required[5].read_text(encoding="utf-8")
    ).get("documents", [])

    if not projects:
        errors.append("No project was created")

    if len(milestones) < 3:
        errors.append("Expected at least three milestones")

    if not documents:
        errors.append("No project document was registered")

    if projects:
        latest = projects[-1]

        if latest.get("customer_portal_enabled") is not False:
            errors.append("Customer portal enabled automatically")

        if latest.get("external_file_sharing_enabled") is not False:
            errors.append("External file sharing enabled automatically")

except Exception as exc:
    errors.append(f"Project memory error: {exc}")

print("--------------------------------------------")
print("Phase 16 Step 4 verification")
print(f"Errors: {len(errors)}")
print("Warnings: 0")

for error in errors:
    print(f"ERROR: {error}")

if errors:
    raise SystemExit(1)
PY

echo
echo "============================================================"
echo " PHASE 16 STEP 4 INSTALLED"
echo " Errors: 0"
echo " Warnings: 0"
echo "============================================================"
echo
echo "Commands:"
echo "  python companyos/projectctl create-from-latest-quote"
echo "  python companyos/projectctl create \"CUSTOMER\" \"PROJECT\" AMOUNT"
echo "  python companyos/projectctl add-milestone PROJECT_ID \"TITLE\" \"DESCRIPTION\""
echo "  python companyos/projectctl set-milestone MILESTONE_ID completed"
echo "  python companyos/projectctl add-document PROJECT_ID \"NAME\" PATH TYPE"
echo "  python companyos/projectctl projects"
echo "  python companyos/projectctl milestones"
echo "  python companyos/projectctl status"
