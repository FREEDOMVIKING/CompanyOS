#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path.home() / "companyos"
MEMORY = ROOT / "ceo_memory"
REPORT = MEMORY / "end_to_end_test_report.json"

errors: list[str] = []
warnings: list[str] = []
passed: list[str] = []
steps: list[dict[str, Any]] = []


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temp.replace(path)


def run(name: str, command: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
    )

    result = {
        "name": name,
        "command": command,
        "return_code": proc.returncode,
        "stdout": proc.stdout[-6000:],
        "stderr": proc.stderr[-3000:],
    }

    steps.append(result)

    if proc.returncode == 0:
        passed.append(name)
    else:
        errors.append(f"{name} failed with code {proc.returncode}")

    return result


def ensure_sample_data() -> None:
    invoices = MEMORY / "invoice_registry.json"
    projects = MEMORY / "project_registry.json"
    tasks = MEMORY / "product_execution_tasks.json"

    invoice_store = load_json(
        invoices,
        {"schema_version": 1, "invoices": []},
    )

    if not any(
        item.get("id") == "e2e-invoice-001"
        for item in invoice_store.get("invoices", [])
    ):
        invoice_store.setdefault("invoices", []).append({
            "id": "e2e-invoice-001",
            "customer_name": "E2E Test Customer",
            "amount": 1250.0,
            "balance_due": 1250.0,
            "status": "sent",
            "created_at": now(),
        })
        save_json(invoices, invoice_store)

    project_store = load_json(
        projects,
        {"schema_version": 1, "projects": []},
    )

    if not any(
        item.get("id") == "e2e-project-001"
        for item in project_store.get("projects", [])
    ):
        project_store.setdefault("projects", []).append({
            "id": "e2e-project-001",
            "project_name": "E2E Test Project",
            "customer_name": "E2E Test Customer",
            "amount": 5000.0,
            "status": "in_progress",
            "progress_percent": 35,
            "created_at": now(),
        })
        save_json(projects, project_store)

    task_store = load_json(
        tasks,
        {"schema_version": 1, "tasks": []},
    )

    if not any(
        item.get("id") == "e2e-task-001"
        for item in task_store.get("tasks", [])
    ):
        task_store.setdefault("tasks", []).append({
            "id": "e2e-task-001",
            "name": "Review E2E test project",
            "description": "Validate the end-to-end CompanyOS workflow.",
            "status": "pending",
            "priority": 80,
            "created_at": now(),
        })
        save_json(tasks, task_store)

    passed.append("Sample business data created")


def verify_outputs() -> None:
    required = [
        MEMORY / "executive_priority_rankings.json",
        MEMORY / "ceo_decision_queue.json",
        MEMORY / "continuous_improvement_findings.json",
        MEMORY / "performance_analytics_metrics.json",
        MEMORY / "business_forecasting_results.json",
    ]

    for path in required:
        if not path.exists():
            errors.append(f"Missing output: {path.name}")
            continue

        data = load_json(path, None)
        if data is None:
            errors.append(f"Invalid output JSON: {path.name}")
        else:
            passed.append(f"Output verified: {path.name}")

    forecast = load_json(
        MEMORY / "business_forecasting_results.json",
        {},
    ).get("forecast", {})

    scenarios = forecast.get("cash_inflow_scenarios", {})
    expected = scenarios.get("expected")

    if expected is None:
        errors.append("Forecast expected scenario missing")
    else:
        passed.append("Forecast expected scenario generated")

    priorities = load_json(
        MEMORY / "executive_priority_rankings.json",
        {},
    ).get("rankings", {}).get("priorities", [])

    if not priorities:
        errors.append("No priorities generated")
    else:
        passed.append(f"{len(priorities)} priorities generated")


def verify_safety() -> None:
    configs = [
        MEMORY / "executive_priority_config.json",
        MEMORY / "ceo_decision_config.json",
        MEMORY / "decision_execution_config.json",
        MEMORY / "continuous_improvement_config.json",
        MEMORY / "performance_analytics_config.json",
        MEMORY / "business_forecasting_config.json",
    ]

    fields = [
        "automatic_task_execution",
        "automatic_customer_contact",
        "automatic_external_execution",
        "automatic_publication",
        "automatic_spending",
    ]

    for path in configs:
        data = load_json(path, {})

        for field in fields:
            if field in data and data[field] is not False:
                errors.append(
                    f"Safety failure: {path.name}: {field} must be false"
                )

    if not any("Safety failure" in item for item in errors):
        passed.append("Safety controls verified")


def main() -> int:
    ensure_sample_data()

    commands = [
        (
            "Opportunity discovery",
            [sys.executable, "companyos/opportunitydiscoveryctl", "discover"],
        ),
        (
            "Executive priority ranking",
            [sys.executable, "companyos/priorityctl", "rank"],
        ),
        (
            "CEO decision preparation",
            [sys.executable, "companyos/decisionctl", "prepare"],
        ),
        (
            "Continuous improvement analysis",
            [sys.executable, "companyos/improvementctl", "analyze"],
        ),
        (
            "Performance analytics",
            [sys.executable, "companyos/performancectl", "collect"],
        ),
        (
            "Business forecasting",
            [sys.executable, "companyos/forecastctl", "forecast"],
        ),
    ]

    for name, command in commands:
        path = ROOT / command[1]

        if not path.exists():
            errors.append(f"Missing command: {command[1]}")
            continue

        run(name, command)

    verify_outputs()
    verify_safety()

    report = {
        "generated_at": now(),
        "summary": {
            "passed": len(passed),
            "warnings": len(warnings),
            "errors": len(errors),
        },
        "passed_checks": passed,
        "warnings": warnings,
        "errors": errors,
        "steps": steps,
        "safety": {
            "automatic_task_execution": False,
            "automatic_customer_contact": False,
            "automatic_external_execution": False,
            "automatic_publication": False,
            "automatic_spending": False,
        },
    }

    save_json(REPORT, report)

    print("------------------------------------------------------------")
    print("CompanyOS End-to-End Test Results")
    print(f"Passed:   {len(passed)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Errors:   {len(errors)}")
    print("------------------------------------------------------------")

    for warning in warnings:
        print(f"WARNING: {warning}")

    for error in errors:
        print(f"ERROR: {error}")

    print(f"Full report: {REPORT}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
