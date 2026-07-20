#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(os.environ.get("COMPANYOS_ROOT", Path.home() / "companyos")).resolve()

PHASES = [
    ("53_60", "PHASE53_60_INSTALLED.json", "scripts/phase53_60_verify.py"),
    ("61_68", "PHASE61_68_INSTALLED.json", "scripts/phase61_68_verify.py"),
    ("69_76", "PHASE69_76_INSTALLED.json", "scripts/phase69_76_verify.py"),
    ("77_84", "PHASE77_84_INSTALLED.json", "scripts/phase77_84_verify.py"),
    ("85_92", "PHASE85_92_INSTALLED.json", "scripts/phase85_92_verify.py"),
    ("93_100", "PHASE93_100_INSTALLED.json", "scripts/phase93_100_verify.py"),
    ("101_108", "PHASE101_108_INSTALLED.json", "scripts/phase101_108_verify.py"),
    ("109_116", "PHASE109_116_INSTALLED.json", "scripts/phase109_116_verify.py"),
    ("117_124", "PHASE117_124_INSTALLED.json", "scripts/phase117_124_verify.py"),
]

EXCLUDED_DIRS = {
    "backups", ".git", ".venv", "venv", "__pycache__", "site-packages",
    ".pytest_cache", ".mypy_cache", ".ruff_cache"
}

def run(cmd, timeout=180):
    try:
        p = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=os.environ.copy(),
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": p.stdout[-8000:],
            "stderr": p.stderr[-8000:],
        }
    except Exception as e:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": f"{type(e).__name__}: {e}",
        }

def active_python_files():
    out = []
    for p in ROOT.rglob("*.py"):
        try:
            rel_parts = p.relative_to(ROOT).parts
        except Exception:
            rel_parts = p.parts
        if any(part in EXCLUDED_DIRS for part in rel_parts):
            continue
        out.append(str(p))
    return sorted(out)

def main():
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "python": sys.version.split()[0],
        "checks": {},
        "phase_checks": [],
    }

    report["checks"]["root_exists"] = ROOT.exists()
    report["checks"]["scripts_dir_exists"] = (ROOT / "scripts").exists()
    report["checks"]["tests_dir_exists"] = (ROOT / "tests").exists()

    py_files = active_python_files()
    report["checks"]["active_python_file_count"] = len(py_files)

    if py_files:
        syntax = run([sys.executable, "-m", "py_compile", *py_files], timeout=240)
    else:
        syntax = {"ok": False, "returncode": -1, "stdout": "", "stderr": "No active Python files found"}
    report["checks"]["python_syntax"] = syntax

    for phase, marker, verifier in PHASES:
        marker_path = ROOT / marker
        verifier_path = ROOT / verifier
        item = {
            "phase": phase,
            "marker_present": marker_path.exists(),
            "verifier_present": verifier_path.exists(),
            "result": None,
        }
        if marker_path.exists() and verifier_path.exists():
            item["result"] = run([sys.executable, str(verifier_path)], timeout=120)
        report["phase_checks"].append(item)

    pytest_probe = run([sys.executable, "-c", "import pytest; print(pytest.__version__)"], timeout=30)
    report["checks"]["pytest_available"] = pytest_probe["ok"]

    if pytest_probe["ok"] and (ROOT / "tests").exists():
        report["checks"]["pytest"] = run(
            [sys.executable, "-m", "pytest", "-q", "tests", "--disable-warnings"],
            timeout=300,
        )

    failed = []
    if not report["checks"]["root_exists"]:
        failed.append("root_exists")
    if not syntax["ok"]:
        failed.append("python_syntax")

    for item in report["phase_checks"]:
        if item["marker_present"]:
            if not item["verifier_present"]:
                failed.append(f'phase_{item["phase"]}_verifier_missing')
            elif not item["result"]["ok"]:
                failed.append(f'phase_{item["phase"]}_verification_failed')

    if report["checks"].get("pytest_available"):
        pytest_result = report["checks"].get("pytest")
        if pytest_result and not pytest_result["ok"]:
            failed.append("pytest")

    installed = [x["phase"] for x in report["phase_checks"] if x["marker_present"]]
    report["installed_phase_bundles"] = installed
    report["success"] = not failed
    report["failed_checks"] = failed
    report["status"] = "full_system_check_passed" if not failed else "full_system_check_failed"

    out = ROOT / "FULL_SYSTEM_CHECK_REPORT.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=" * 68)
    print("COMPANYOS FULL SYSTEM CHECK V2")
    print("=" * 68)
    print(f"Root: {ROOT}")
    print(f"Active Python files checked: {len(py_files)}")
    print("Excluded from syntax scan: backups, virtualenv/vendor/cache directories")
    print(f'Python syntax: {"PASS" if syntax["ok"] else "FAIL"}')

    for item in report["phase_checks"]:
        if not item["marker_present"]:
            print(f'Phase {item["phase"]}: NOT INSTALLED')
        elif not item["verifier_present"]:
            print(f'Phase {item["phase"]}: FAIL (verifier missing)')
        else:
            print(f'Phase {item["phase"]}: {"PASS" if item["result"]["ok"] else "FAIL"}')

    if report["checks"].get("pytest_available"):
        print(f'Pytest: {"PASS" if report["checks"]["pytest"]["ok"] else "FAIL"}')
        if report["checks"]["pytest"]["stdout"]:
            last = report["checks"]["pytest"]["stdout"].strip().splitlines()[-1]
            print(f"Pytest summary: {last}")
    else:
        print("Pytest: SKIPPED")

    print("-" * 68)
    print(json.dumps({
        "success": report["success"],
        "status": report["status"],
        "failed_checks": report["failed_checks"],
        "report": str(out),
    }, indent=2))
    sys.exit(0 if report["success"] else 1)

if __name__ == "__main__":
    main()
