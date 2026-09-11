#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required_files = [
    ROOT / "agents/phase51_execution_planner/execution_planner.py",
    ROOT / "agents/phase51_execution_planner/task_dispatcher.py",
    ROOT / "agents/phase51_execution_planner/task_executor.py",
    ROOT / "agents/phase51_execution_planner/execution_loop.py",
    ROOT / "companyos/phase51ctl",
    ROOT / "ceo_memory/phase51/phase51_config.json",
]

errors = []
checks = []

for path in required_files:
    ok = path.exists()
    checks.append({
        "check": f"file:{path.relative_to(ROOT)}",
        "passed": ok
    })
    if not ok:
        errors.append(f"Missing required file: {path}")

compile_targets = [p for p in required_files if p.suffix == ".py"]

for path in compile_targets:
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(path)],
        capture_output=True,
        text=True
    )

    ok = result.returncode == 0

    checks.append({
        "check": f"compile:{path.relative_to(ROOT)}",
        "passed": ok
    })

    if not ok:
        errors.append(
            f"Compile failed: {path}\n"
            f"{result.stderr}"
        )

config_path = ROOT / "ceo_memory/phase51/phase51_config.json"

if config_path.exists():
    try:
        config = json.loads(config_path.read_text())

        rules = config.get("rules", {})

        safety_ok = (
            rules.get(
                "require_owner_approval_for_financial_commitments"
            ) is True
            and rules.get(
                "require_owner_approval_for_irreversible_external_actions"
            ) is True
            and rules.get(
                "allow_autonomous_reversible_internal_actions"
            ) is True
        )

        checks.append({
            "check": "phase51_safety_boundaries",
            "passed": safety_ok
        })

        if not safety_ok:
            errors.append(
                "Phase 51 safety boundaries are missing or invalid"
            )

    except Exception as exc:
        errors.append(f"Config validation failed: {exc}")

success = len(errors) == 0

print(json.dumps({
    "success": success,
    "status": (
        "phase51_verification_passed"
        if success
        else "phase51_verification_failed"
    ),
    "checks": checks,
    "errors": errors
}, indent=2))

raise SystemExit(0 if success else 1)
