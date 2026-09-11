#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail

ROOT="$HOME/companyos"
REPORT_DIR="$ROOT/ceo_memory"
REPORT="$REPORT_DIR/companyos_integration_test.json"
TMP="$(mktemp)"
ERRORS=0
WARNINGS=0
PASSED=0

mkdir -p "$REPORT_DIR"
cd "$ROOT" || {
  echo "CompanyOS folder not found: $ROOT"
  exit 1
}

echo "============================================================"
echo " CompanyOS Full Integration Test"
echo "============================================================"

python - "$ROOT" "$REPORT" <<'PY'
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

root = Path(sys.argv[1])
report_path = Path(sys.argv[2])

errors: list[str] = []
warnings: list[str] = []
passed: list[str] = []
module_results: list[dict[str, Any]] = []

def check(condition: bool, success: str, failure: str, warning: bool = False) -> None:
    if condition:
        passed.append(success)
    elif warning:
        warnings.append(failure)
    else:
        errors.append(failure)

def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid JSON: {path.relative_to(root)}: {exc}")
        return None

required_dirs = [
    root / "agents",
    root / "companyos",
    root / "ceo_memory",
]

for directory in required_dirs:
    check(
        directory.is_dir(),
        f"Directory exists: {directory.relative_to(root)}",
        f"Missing directory: {directory.relative_to(root)}",
    )

modules = [
    ("CRM", "crmctl", None),
    ("Quotes", "quotectl", None),
    ("Sales", "salesctl", None),
    ("Projects", "projectctl", None),
    ("Automation", "automationctl", None),
    ("Accounting", "accountingctl", None),
    ("AI Executive", "executivectl", None),
    ("Opportunity Discovery", "opportunitydiscoveryctl", None),
    ("Executive Priority", "priorityctl", "status"),
    ("CEO Decision", "decisionctl", "status"),
    ("Execution Planner", "executionplanctl", "status"),
    ("Continuous Improvement", "improvementctl", "status"),
    ("Performance Analytics", "performancectl", "status"),
    ("Business Forecasting", "forecastctl", "status"),
    ("GitHub Control", "githubctl", None),
]

for name, command, action in modules:
    path = root / "companyos" / command
    exists = path.is_file()
    executable = path.exists() and bool(path.stat().st_mode & 0o111)

    check(
        exists,
        f"{name}: command exists",
        f"{name}: missing companyos/{command}",
    )

    if exists:
        check(
            executable,
            f"{name}: command executable",
            f"{name}: command is not executable",
            warning=True,
        )

        try:
            py_compile.compile(str(path), doraise=True)
            passed.append(f"{name}: Python compile passed")
        except Exception as exc:
            errors.append(f"{name}: compile failed: {exc}")

    result: dict[str, Any] = {
        "name": name,
        "command": command,
        "exists": exists,
        "executable": executable,
        "status_tested": False,
    }

    if exists and action:
        proc = subprocess.run(
            [sys.executable, str(path), action],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=30,
        )
        result["status_tested"] = True
        result["return_code"] = proc.returncode
        result["stdout"] = proc.stdout[-4000:]
        result["stderr"] = proc.stderr[-2000:]

        if proc.returncode == 0:
            passed.append(f"{name}: status command passed")
        else:
            errors.append(
                f"{name}: status command failed with code {proc.returncode}"
            )

        try:
            payload = json.loads(proc.stdout)
            result["valid_json_output"] = True
            if payload.get("success") is not True:
                warnings.append(f"{name}: status returned success != true")
        except Exception:
            result["valid_json_output"] = False
            warnings.append(f"{name}: status output was not valid JSON")

    module_results.append(result)

json_files = list((root / "ceo_memory").glob("*.json"))
check(
    bool(json_files),
    f"Found {len(json_files)} memory JSON files",
    "No JSON memory files found",
)

for path in json_files:
    load_json(path)

safety_files = [
    root / "ceo_memory" / "executive_priority_config.json",
    root / "ceo_memory" / "ceo_decision_config.json",
    root / "ceo_memory" / "decision_execution_config.json",
    root / "ceo_memory" / "continuous_improvement_config.json",
    root / "ceo_memory" / "performance_analytics_config.json",
    root / "ceo_memory" / "business_forecasting_config.json",
]

safety_fields = [
    "automatic_task_execution",
    "automatic_customer_contact",
    "automatic_external_execution",
    "automatic_publication",
    "automatic_spending",
]

for path in safety_files:
    if not path.exists():
        warnings.append(f"Safety config missing: {path.name}")
        continue

    data = load_json(path)
    if not isinstance(data, dict):
        continue

    for field in safety_fields:
        if field in data:
            check(
                data[field] is False,
                f"{path.name}: {field}=false",
                f"SAFETY FAILURE: {path.name}: {field} is not false",
            )

agent_files = list((root / "agents").glob("*.py"))
for path in agent_files:
    try:
        py_compile.compile(str(path), doraise=True)
        passed.append(f"Agent compile passed: {path.name}")
    except Exception as exc:
        errors.append(f"Agent compile failed: {path.name}: {exc}")

git_dir = root / ".git"
check(
    git_dir.exists(),
    "Git repository detected",
    "No .git repository detected",
)

if git_dir.exists():
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if proc.returncode == 0:
        if proc.stdout.strip():
            warnings.append("Git working tree has uncommitted changes")
        else:
            passed.append("Git working tree is clean")
    else:
        errors.append("git status failed")

report = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "root": str(root),
    "summary": {
        "passed": len(passed),
        "warnings": len(warnings),
        "errors": len(errors),
    },
    "passed_checks": passed,
    "warnings": warnings,
    "errors": errors,
    "modules": module_results,
}

report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

print("------------------------------------------------------------")
print("CompanyOS Integration Test Results")
print(f"Passed:   {len(passed)}")
print(f"Warnings: {len(warnings)}")
print(f"Errors:   {len(errors)}")
print("------------------------------------------------------------")

if warnings:
    print("WARNINGS:")
    for item in warnings:
        print(f"  - {item}")

if errors:
    print("ERRORS:")
    for item in errors:
        print(f"  - {item}")

print("------------------------------------------------------------")
print(f"Full report: {report_path}")

raise SystemExit(1 if errors else 0)
PY

EXIT_CODE=$?

echo
if [ "$EXIT_CODE" -eq 0 ]; then
  echo "============================================================"
  echo " COMPANYOS INTEGRATION TEST PASSED"
  echo " Errors: 0"
  echo "============================================================"
else
  echo "============================================================"
  echo " COMPANYOS INTEGRATION TEST FOUND ERRORS"
  echo " Review:"
  echo " $REPORT"
  echo "============================================================"
fi

exit "$EXIT_CODE"
