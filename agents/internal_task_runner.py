#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"
WORKSPACE = ROOT / "workspace"

CONFIG_PATH = MEMORY / "internal_task_runner_config.json"
TASKS_PATH = MEMORY / "product_execution_tasks.json"
PLANS_PATH = MEMORY / "product_execution_plans.json"
RESULTS_PATH = MEMORY / "internal_task_results.json"
HEALTH_PATH = MEMORY / "internal_task_runner_health.json"
AUDIT_PATH = MEMORY / "internal_task_runner_audit.json"


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
        json.dumps(
            value,
            indent=2,
            sort_keys=False,
        ),
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

    save_json(AUDIT_PATH, records[-1000:])


def safe_name(value: str) -> str:
    cleaned = re.sub(
        r"[^a-zA-Z0-9._-]+",
        "_",
        value.strip(),
    )

    return cleaned.strip("_") or "project"


def project_directory(task: dict[str, Any]) -> Path:
    project_name = safe_name(
        str(
            task.get("project_name")
            or task.get("project_id")
            or "project"
        )
    )

    path = WORKSPACE / project_name
    path.mkdir(parents=True, exist_ok=True)

    return path


def task_dependencies_complete(
    task: dict[str, Any],
    tasks: list[dict[str, Any]],
) -> bool:
    dependencies = task.get("blocked_by", [])

    if not dependencies:
        return True

    statuses = {
        item.get("id"): item.get("status")
        for item in tasks
    }

    return all(
        statuses.get(dependency) == "completed"
        for dependency in dependencies
    )


def ready_tasks(
    selected_plan: str | None = None,
) -> list[dict[str, Any]]:
    store = load_json(TASKS_PATH, {})
    tasks = store.get("tasks", [])

    results = [
        task
        for task in tasks
        if task.get("status") == "pending"
        and (
            selected_plan is None
            or task.get("plan_id") == selected_plan
        )
        and task_dependencies_complete(task, tasks)
    ]

    results.sort(
        key=lambda item: (
            -int(item.get("priority", 0)),
            int(item.get("order", 999)),
        )
    )

    return results


def markdown_header(
    task: dict[str, Any],
    title: str,
) -> str:
    return "\n".join([
        f"# {title}",
        "",
        f"Project: {task.get('project_name')}",
        f"Task ID: {task.get('id')}",
        f"Task type: {task.get('type')}",
        f"Created: {now()}",
        "",
    ])


def research_output(task: dict[str, Any]) -> tuple[str, str]:
    filename = "customer_problem_validation.md"

    content = markdown_header(
        task,
        "Customer and Problem Validation Plan",
    )

    content += "\n".join([
        "## Target customer",
        "",
        "Primary target: small residential and light-commercial contractors.",
        "",
        "Likely users include:",
        "",
        "- Owner-operators",
        "- Estimators",
        "- Project managers",
        "- Office administrators",
        "",
        "## Core problem assumptions",
        "",
        "- Bid information is scattered across texts, notes and paper.",
        "- Follow-ups are inconsistent.",
        "- Contractors lose track of bid status.",
        "- Existing software may be too complex or expensive.",
        "",
        "## Validation questions",
        "",
        "1. How do you currently track leads and bids?",
        "2. How many estimates do you prepare each month?",
        "3. What causes bids to be forgotten or delayed?",
        "4. How often do you follow up after sending an estimate?",
        "5. What would make a bid organizer worth paying for?",
        "6. Would you prefer a setup fee, monthly plan or one-time price?",
        "",
        "## Success criteria",
        "",
        "- At least 5 customer conversations completed.",
        "- At least 3 customers confirm the problem happens weekly.",
        "- At least 2 customers show willingness to test an MVP.",
        "- At least 1 pricing model receives positive interest.",
        "",
        "## Go or hold rule",
        "",
        "Proceed if the problem is frequent, costly and confirmed by multiple contractors.",
        "",
    ])

    return filename, content


def design_output(task: dict[str, Any]) -> tuple[str, str]:
    name = str(task.get("name", "")).lower()

    if "requirements" in name:
        filename = "product_requirements.md"

        content = markdown_header(
            task,
            "Product Requirements Document",
        )

        content += "\n".join([
            "## Product goal",
            "",
            "Give small contractors one simple place to track leads, bids, follow-ups and job notes.",
            "",
            "## Core MVP capabilities",
            "",
            "- Create and edit customer records",
            "- Create and track bids",
            "- Assign bid status",
            "- Record follow-up dates",
            "- Store job notes",
            "- Display a simple pipeline dashboard",
            "",
            "## Initial statuses",
            "",
            "- New lead",
            "- Estimate needed",
            "- Estimate sent",
            "- Follow-up due",
            "- Won",
            "- Lost",
            "",
            "## Acceptance criteria",
            "",
            "- A user can create a lead.",
            "- A user can attach an estimate amount.",
            "- A user can change bid status.",
            "- A user can record a follow-up date.",
            "- A user can view all active bids.",
            "- Data persists locally.",
            "",
            "## Out of scope for MVP",
            "",
            "- Payment processing",
            "- Automatic email sending",
            "- Public hosting",
            "- Paid integrations",
            "- Automatic external publication",
            "",
        ])

        return filename, content

    filename = "core_user_workflow.md"

    content = markdown_header(
        task,
        "Core User Workflow",
    )

    content += "\n".join([
        "## Main workflow",
        "",
        "1. Open dashboard.",
        "2. Add a new customer or lead.",
        "3. Enter project and estimate details.",
        "4. Set bid status.",
        "5. Add next follow-up date.",
        "6. Review due follow-ups.",
        "7. Update bid to won or lost.",
        "",
        "## Primary screens",
        "",
        "- Dashboard",
        "- Lead list",
        "- Lead details",
        "- Bid form",
        "- Follow-up list",
        "- Settings",
        "",
        "## Error states",
        "",
        "- Missing customer name",
        "- Invalid estimate amount",
        "- Invalid date",
        "- Missing local storage",
        "- Duplicate record warning",
        "",
    ])

    return filename, content


def development_output(task: dict[str, Any]) -> tuple[str, str]:
    name = str(task.get("name", "")).lower()
    project_dir = project_directory(task)

    if "data model" in name:
        filename = "data_model.json"

        content = json.dumps(
            {
                "entities": {
                    "customers": {
                        "fields": [
                            "id",
                            "name",
                            "phone",
                            "email",
                            "address",
                            "created_at",
                            "updated_at"
                        ]
                    },
                    "bids": {
                        "fields": [
                            "id",
                            "customer_id",
                            "project_name",
                            "description",
                            "estimate_amount",
                            "status",
                            "follow_up_date",
                            "notes",
                            "created_at",
                            "updated_at"
                        ]
                    },
                    "activity": {
                        "fields": [
                            "id",
                            "bid_id",
                            "activity_type",
                            "details",
                            "created_at"
                        ]
                    }
                },
                "storage": "local_json",
                "external_network_required": False
            },
            indent=2,
        )

        return filename, content

    if "project structure" in name:
        app_dir = project_dir / "app"

        for directory in [
            app_dir,
            app_dir / "data",
            app_dir / "templates",
            app_dir / "static",
            project_dir / "tests",
            project_dir / "docs",
        ]:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

        files = {
            project_dir / "README.md": (
                "# Local Contractor Bid Organizer\n\n"
                "Internal MVP workspace generated by CompanyOS.\n"
            ),
            app_dir / "__init__.py": "",
            app_dir / "main.py": (
                "from __future__ import annotations\n\n"
                "def main() -> None:\n"
                "    print('Local Contractor Bid Organizer MVP')\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            project_dir / "run.py": (
                "from app.main import main\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            project_dir / "requirements.txt": "",
        }

        for path, value in files.items():
            if not path.exists():
                path.write_text(
                    value,
                    encoding="utf-8",
                )

        filename = "project_structure_report.md"

        content = markdown_header(
            task,
            "MVP Project Structure Report",
        )

        content += "\n".join([
            "Created:",
            "",
            "- app/",
            "- app/data/",
            "- app/templates/",
            "- app/static/",
            "- tests/",
            "- docs/",
            "- run.py",
            "- requirements.txt",
            "- README.md",
            "",
            "External network access was not used.",
            "",
        ])

        return filename, content

    filename = "mvp_core_workflow.py"

    content = """from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_PATH = Path(__file__).resolve().parent / "data" / "bids.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_bids() -> list[dict[str, Any]]:
    if not DATA_PATH.exists():
        return []

    try:
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_bids(bids: list[dict[str, Any]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps(bids, indent=2),
        encoding="utf-8",
    )


def add_bid(
    customer_name: str,
    project_name: str,
    estimate_amount: float,
) -> dict[str, Any]:
    if not customer_name.strip():
        raise ValueError("Customer name is required")

    if estimate_amount < 0:
        raise ValueError("Estimate amount cannot be negative")

    bids = load_bids()

    bid = {
        "id": f"bid-{len(bids) + 1}",
        "customer_name": customer_name.strip(),
        "project_name": project_name.strip(),
        "estimate_amount": estimate_amount,
        "status": "new_lead",
        "follow_up_date": None,
        "notes": [],
        "created_at": now(),
        "updated_at": now(),
    }

    bids.append(bid)
    save_bids(bids)

    return bid
"""

    return filename, content


def testing_output(task: dict[str, Any]) -> tuple[str, str]:
    filename = "test_plan.md"

    content = markdown_header(
        task,
        "Internal MVP Test Plan",
    )

    content += "\n".join([
        "## Functional tests",
        "",
        "- Create a customer record",
        "- Create a bid",
        "- Reject empty customer name",
        "- Reject negative estimate amount",
        "- Change bid status",
        "- Save and reload bid data",
        "- Record follow-up date",
        "",
        "## Failure-path tests",
        "",
        "- Missing data file",
        "- Invalid JSON data",
        "- Invalid date",
        "- Duplicate ID",
        "- Unsupported status",
        "",
        "## Pass criteria",
        "",
        "- All core workflow tests pass.",
        "- No task performs external execution.",
        "- No paid service is required.",
        "- No publication occurs.",
        "",
    ])

    return filename, content


def validation_output(task: dict[str, Any]) -> tuple[str, str]:
    filename = "validation_report.md"

    content = markdown_header(
        task,
        "Product Validation Review",
    )

    content += "\n".join([
        "## Current assessment",
        "",
        "The internal MVP plan matches the approved proposal and focuses on the core contractor bid workflow.",
        "",
        "## Strengths",
        "",
        "- Clear target customer",
        "- Strong strategic fit",
        "- Small initial scope",
        "- Local-first design",
        "- Recurring revenue potential",
        "",
        "## Remaining validation needs",
        "",
        "- Customer interviews",
        "- Pricing feedback",
        "- Workflow testing with real contractors",
        "- Confirmation that follow-up reminders are valuable",
        "",
        "## Recommendation",
        "",
        "Continue internal development. Hold external launch until owner review and customer validation are complete.",
        "",
    ])

    return filename, content


def documentation_output(task: dict[str, Any]) -> tuple[str, str]:
    filename = "README.md"

    content = markdown_header(
        task,
        "Local Contractor Bid Organizer",
    )

    content += "\n".join([
        "## Purpose",
        "",
        "A simple internal MVP for tracking contractor leads, estimates, follow-ups and bid status.",
        "",
        "## Current status",
        "",
        "Internal planning and prototype development.",
        "",
        "## Run locally",
        "",
        "```bash",
        "python run.py",
        "```",
        "",
        "## Restrictions",
        "",
        "- No automatic spending",
        "- No automatic publication",
        "- No external execution",
        "- No secret access",
        "- No network access required",
        "",
    ])

    return filename, content


def deployment_output(task: dict[str, Any]) -> tuple[str, str]:
    filename = "deployment_checklist.md"

    content = markdown_header(
        task,
        "Deployment and Launch Checklist",
    )

    content += "\n".join([
        "## Internal readiness",
        "",
        "- [ ] Core workflow complete",
        "- [ ] Tests passing",
        "- [ ] Documentation complete",
        "- [ ] Data backup tested",
        "- [ ] Owner review complete",
        "",
        "## External launch approval",
        "",
        "- [ ] Owner explicitly approves publication",
        "- [ ] Hosting plan reviewed",
        "- [ ] Costs reviewed",
        "- [ ] Privacy requirements reviewed",
        "- [ ] Customer support process prepared",
        "",
        "## Current authorization",
        "",
        "External deployment is not authorized.",
        "",
    ])

    return filename, content


def execute_task_output(
    task: dict[str, Any],
) -> tuple[str, str]:
    task_type = str(task.get("type", ""))

    handlers = {
        "research": research_output,
        "design": design_output,
        "development": development_output,
        "testing": testing_output,
        "validation": validation_output,
        "documentation": documentation_output,
        "deployment_planning": deployment_output,
    }

    handler = handlers.get(task_type)

    if not handler:
        raise ValueError(
            f"Unsupported internal task type: {task_type}"
        )

    return handler(task)


def update_task_statistics(store: dict[str, Any]) -> None:
    tasks = store.get("tasks", [])

    store["statistics"] = {
        "total": len(tasks),
        "pending": sum(
            1 for item in tasks
            if item.get("status") == "pending"
        ),
        "in_progress": sum(
            1 for item in tasks
            if item.get("status") == "in_progress"
        ),
        "completed": sum(
            1 for item in tasks
            if item.get("status") == "completed"
        ),
        "blocked": sum(
            1 for item in tasks
            if item.get("status") == "blocked"
        ),
        "failed": sum(
            1 for item in tasks
            if item.get("status") == "failed"
        ),
    }

    store["last_updated_at"] = now()


def update_plan(
    plan_id_value: str,
    tasks: list[dict[str, Any]],
) -> None:
    store = load_json(PLANS_PATH, {})

    plan_tasks = [
        item
        for item in tasks
        if item.get("plan_id") == plan_id_value
    ]

    for plan in store.get("plans", []):
        if plan.get("id") != plan_id_value:
            continue

        total = len(plan_tasks)

        completed = sum(
            1
            for item in plan_tasks
            if item.get("status") == "completed"
        )

        failed = sum(
            1
            for item in plan_tasks
            if item.get("status") == "failed"
        )

        plan["completed_tasks"] = completed
        plan["progress_percent"] = (
            round(completed / total * 100, 2)
            if total
            else 0
        )

        if completed == total and total:
            plan["status"] = "completed"
            plan["current_phase"] = "complete"
            plan["completed_at"] = now()

        elif failed:
            plan["status"] = "blocked"

        else:
            remaining = [
                item
                for item in plan_tasks
                if item.get("status") != "completed"
            ]

            plan["status"] = (
                "active"
                if completed
                else "planned"
            )

            if remaining:
                plan["current_phase"] = remaining[0].get(
                    "phase",
                    "unknown",
                )

        plan["updated_at"] = now()

    plans = store.get("plans", [])

    store["statistics"] = {
        "total": len(plans),
        "planned": sum(
            1 for item in plans
            if item.get("status") == "planned"
        ),
        "active": sum(
            1 for item in plans
            if item.get("status") == "active"
        ),
        "completed": sum(
            1 for item in plans
            if item.get("status") == "completed"
        ),
        "blocked": sum(
            1 for item in plans
            if item.get("status") == "blocked"
        ),
    }

    store["last_updated_at"] = now()
    save_json(PLANS_PATH, store)


def append_result(result: dict[str, Any]) -> None:
    store = load_json(
        RESULTS_PATH,
        {
            "schema_version": 1,
            "results": [],
            "statistics": {},
        },
    )

    records = store.setdefault("results", [])
    records.append(result)

    records[:] = records[-1000:]

    store["statistics"] = {
        "total": len(records),
        "completed": sum(
            1 for item in records
            if item.get("status") == "completed"
        ),
        "failed": sum(
            1 for item in records
            if item.get("status") == "failed"
        ),
        "blocked": sum(
            1 for item in records
            if item.get("status") == "blocked"
        ),
    }

    store["last_updated_at"] = now()
    save_json(RESULTS_PATH, store)


def run_task(task_id_value: str) -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})

    if not config.get("enabled", True):
        result = {
            "success": False,
            "status": "internal_task_runner_disabled",
        }
        audit("run", result)
        return result

    store = load_json(TASKS_PATH, {})
    tasks = store.get("tasks", [])

    selected = None

    for task in tasks:
        if task.get("id") == task_id_value:
            selected = task
            break

    if not selected:
        result = {
            "success": False,
            "status": "task_not_found",
            "task_id": task_id_value,
        }
        audit("run", result)
        return result

    allowed_types = set(
        config.get("allowed_task_types", [])
    )

    if selected.get("type") not in allowed_types:
        result = {
            "success": False,
            "status": "task_type_blocked",
            "task_id": task_id_value,
            "task_type": selected.get("type"),
        }
        audit("run", result)
        return result

    if selected.get("external_execution_allowed") is not False:
        result = {
            "success": False,
            "status": "unsafe_task_blocked",
            "reason": "External execution flag is not disabled",
            "task_id": task_id_value,
        }
        audit("run", result)
        return result

    if not task_dependencies_complete(selected, tasks):
        result = {
            "success": False,
            "status": "task_dependency_blocked",
            "task_id": task_id_value,
            "blocked_by": selected.get("blocked_by", []),
        }
        audit("run", result)
        return result

    selected["status"] = "in_progress"
    selected["started_at"] = now()
    selected["updated_at"] = now()
    selected["attempts"] = int(
        selected.get("attempts", 0)
    ) + 1

    save_json(TASKS_PATH, store)

    try:
        filename, content = execute_task_output(selected)

        directory = project_directory(selected)
        output_path = directory / filename

        output_path.write_text(
            content,
            encoding="utf-8",
        )

        selected["status"] = "completed"
        selected["completed_at"] = now()
        selected["updated_at"] = now()
        selected["last_error"] = None
        selected["result"] = {
            "output_file": str(output_path),
            "task_runner": "internal_task_runner",
            "network_used": False,
            "shell_execution_used": False,
            "external_execution_used": False,
            "external_spending_used": False,
            "external_publication_used": False,
        }

        update_task_statistics(store)
        save_json(TASKS_PATH, store)

        update_plan(
            str(selected.get("plan_id")),
            tasks,
        )

        record = {
            "id": f"result-{task_id_value}",
            "task_id": task_id_value,
            "plan_id": selected.get("plan_id"),
            "project_id": selected.get("project_id"),
            "project_name": selected.get("project_name"),
            "task_name": selected.get("name"),
            "task_type": selected.get("type"),
            "status": "completed",
            "output_file": str(output_path),
            "network_used": False,
            "shell_execution_used": False,
            "external_execution_used": False,
            "external_spending_used": False,
            "external_publication_used": False,
            "completed_at": now(),
        }

        append_result(record)

        result = {
            "success": True,
            "status": "internal_task_completed",
            "task_id": task_id_value,
            "task_name": selected.get("name"),
            "task_type": selected.get("type"),
            "output_file": str(output_path),
            "network_used": False,
            "shell_execution_used": False,
            "external_execution_used": False,
            "external_spending_used": False,
            "external_publication_used": False,
        }

    except Exception as exc:
        selected["status"] = "failed"
        selected["last_error"] = str(exc)
        selected["updated_at"] = now()

        update_task_statistics(store)
        save_json(TASKS_PATH, store)

        update_plan(
            str(selected.get("plan_id")),
            tasks,
        )

        append_result({
            "id": f"result-{task_id_value}-{selected['attempts']}",
            "task_id": task_id_value,
            "plan_id": selected.get("plan_id"),
            "status": "failed",
            "error": str(exc),
            "completed_at": now(),
        })

        result = {
            "success": False,
            "status": "internal_task_failed",
            "task_id": task_id_value,
            "error": str(exc),
        }

    save_json(
        HEALTH_PATH,
        {
            "healthy": result.get("success", False),
            "last_run_at": now(),
            "last_task_id": task_id_value,
            "last_error": result.get("error"),
        },
    )

    audit("run", result)
    return result


def run_next(
    plan_id_value: str | None = None,
) -> dict[str, Any]:
    tasks = ready_tasks(plan_id_value)

    if not tasks:
        result = {
            "success": False,
            "status": "no_ready_internal_tasks",
            "plan_id": plan_id_value,
        }
        audit("run_next", result)
        return result

    return run_task(str(tasks[0].get("id")))


def run_all_ready(
    plan_id_value: str | None = None,
) -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})
    maximum = int(
        config.get("maximum_tasks_per_run", 10)
    )

    completed = 0
    failed = 0
    results: list[dict[str, Any]] = []

    for _ in range(maximum):
        tasks = ready_tasks(plan_id_value)

        if not tasks:
            break

        result = run_task(
            str(tasks[0].get("id"))
        )

        results.append(result)

        if result.get("success"):
            completed += 1
        else:
            failed += 1
            break

    final = {
        "success": failed == 0,
        "status": "internal_task_batch_complete",
        "plan_id": plan_id_value,
        "completed": completed,
        "failed": failed,
        "maximum_tasks_per_run": maximum,
        "results": results,
        "automatic_external_execution": False,
        "automatic_spending": False,
        "automatic_publication": False,
    }

    audit("run_all", final)
    return final


def status() -> dict[str, Any]:
    config = load_json(CONFIG_PATH, {})
    tasks = load_json(TASKS_PATH, {})
    plans = load_json(PLANS_PATH, {})
    results = load_json(RESULTS_PATH, {})
    health = load_json(HEALTH_PATH, {})

    output = {
        "success": True,
        "status": "internal_task_runner_status",
        "enabled": config.get("enabled", False),
        "automatic_internal_execution": config.get(
            "automatic_internal_execution",
            False,
        ),
        "allow_shell_execution": config.get(
            "allow_shell_execution",
            False,
        ),
        "allow_network_access": config.get(
            "allow_network_access",
            False,
        ),
        "allow_secret_access": config.get(
            "allow_secret_access",
            False,
        ),
        "automatic_external_execution": config.get(
            "automatic_external_execution",
            False,
        ),
        "automatic_spending": config.get(
            "automatic_spending",
            False,
        ),
        "automatic_publication": config.get(
            "automatic_publication",
            False,
        ),
        "task_statistics": tasks.get(
            "statistics",
            {},
        ),
        "plan_statistics": plans.get(
            "statistics",
            {},
        ),
        "result_statistics": results.get(
            "statistics",
            {},
        ),
        "ready_tasks": len(ready_tasks()),
        "health": health,
    }

    audit("status", output)
    return output


def list_results() -> dict[str, Any]:
    store = load_json(RESULTS_PATH, {})

    result = {
        "success": True,
        "status": "internal_task_result_list",
        "statistics": store.get("statistics", {}),
        "results": store.get("results", []),
    }

    audit("results", result)
    return result


def print_result(result: dict[str, Any]) -> int:
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: internal_task_runner.py "
            "run <task_id>|next [plan_id]|"
            "run-all [plan_id]|status|results"
        )
        return 2

    action = sys.argv[1].lower()

    try:
        if action == "run":
            if len(sys.argv) < 3:
                raise ValueError("Task ID is required")

            return print_result(
                run_task(sys.argv[2])
            )

        if action == "next":
            selected_plan = (
                sys.argv[2]
                if len(sys.argv) > 2
                else None
            )

            return print_result(
                run_next(selected_plan)
            )

        if action == "run-all":
            selected_plan = (
                sys.argv[2]
                if len(sys.argv) > 2
                else None
            )

            return print_result(
                run_all_ready(selected_plan)
            )

        if action == "status":
            return print_result(status())

        if action == "results":
            return print_result(list_results())

        return print_result({
            "success": False,
            "status": "unknown_internal_task_action",
            "action": action,
        })

    except Exception as exc:
        result = {
            "success": False,
            "status": "internal_task_runner_error",
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
