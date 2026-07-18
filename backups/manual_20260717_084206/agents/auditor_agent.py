#!/usr/bin/env python3

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = BASE_DIR / "company_builds"
AUDIT_DIR = BASE_DIR / "ceo_memory" / "audits"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_project_path(project_slug: str) -> Path:
    project_path = (BUILD_DIR / project_slug).resolve()
    build_root = BUILD_DIR.resolve()

    if project_path.parent != build_root:
        raise ValueError("Invalid project path")

    return project_path


def run_python_test(
    test_file: Path,
    project_dir: Path,
) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [sys.executable, test_file.name],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = (result.stdout + result.stderr).strip()

        return {
            "passed": result.returncode == 0,
            "return_code": result.returncode,
            "output": output,
        }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "return_code": None,
            "output": "Test timed out after 30 seconds",
        }

    except Exception as error:
        return {
            "passed": False,
            "return_code": None,
            "output": str(error),
        }


def audit_project(task: dict[str, Any]) -> dict[str, Any]:
    payload = task.get("payload", {})
    project_slug = payload.get("project_slug", "").strip()

    if not project_slug:
        return {
            "success": False,
            "error": "project_slug is required",
        }

    try:
        project_dir = safe_project_path(project_slug)
    except ValueError as error:
        return {
            "success": False,
            "error": str(error),
        }

    if not project_dir.exists():
        return {
            "success": False,
            "error": f"Project does not exist: {project_slug}",
        }

    required_files = [
        "README.md",
        "app.py",
        "test_app.py",
        "manifest.json",
    ]

    missing_files = [
        name
        for name in required_files
        if not (project_dir / name).exists()
    ]

    checks = {
        "required_files_present": not missing_files,
        "missing_files": missing_files,
        "manifest_valid": False,
        "syntax_valid": False,
        "tests_passed": False,
        "test_output": "",
    }

    manifest_file = project_dir / "manifest.json"

    if manifest_file.exists():
        try:
            with manifest_file.open("r", encoding="utf-8") as file:
                json.load(file)

            checks["manifest_valid"] = True
        except (json.JSONDecodeError, OSError):
            checks["manifest_valid"] = False

    app_file = project_dir / "app.py"

    if app_file.exists():
        syntax_result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(app_file)],
            capture_output=True,
            text=True,
        )

        checks["syntax_valid"] = syntax_result.returncode == 0

        if syntax_result.returncode != 0:
            checks["syntax_error"] = syntax_result.stderr.strip()

    test_file = project_dir / "test_app.py"

    if test_file.exists():
        test_result = run_python_test(
            test_file=test_file,
            project_dir=project_dir,
        )

        checks["tests_passed"] = test_result["passed"]
        checks["test_output"] = test_result["output"]

    approved = all([
        checks["required_files_present"],
        checks["manifest_valid"],
        checks["syntax_valid"],
        checks["tests_passed"],
    ])

    report = {
        "project_slug": project_slug,
        "project_id": task.get("project_id"),
        "approved": approved,
        "checks": checks,
        "audited_at": now(),
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    report_file = AUDIT_DIR / f"{project_slug}_audit.json"

    with report_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    return {
        "success": approved,
        "status": "approved" if approved else "rejected",
        "report": report,
        "report_file": str(report_file),
        "error": None if approved else "Project failed one or more audit checks",
    }


def run_task(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")

    if action != "audit_project":
        return {
            "success": False,
            "error": f"Unsupported auditor action: {action}",
        }

    return audit_project(task)


if __name__ == "__main__":
    sample_task = {
        "id": "sample-audit-task",
        "action": "audit_project",
        "project_id": "project-1",
        "payload": {
            "project_slug": "digital_template_business",
        },
    }

    print(json.dumps(run_task(sample_task), indent=2))
