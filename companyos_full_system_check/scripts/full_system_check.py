#!/usr/bin/env python3
from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

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

def run(cmd, timeout=120):
    try:
        p = subprocess.run(
            cmd, cwd=ROOT, text=True, capture_output=True,
            timeout=timeout, env=os.environ.copy()
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": p.stdout[-5000:],
            "stderr": p.stderr[-5000:],
        }
    except Exception as e:
        return {"ok": False, "returncode": -1, "stdout": "", "stderr": f"{type(e).__name__}: {e}"}

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
    report["checks"]["state_dir_exists"] = (ROOT / "state").exists()

    # Syntax compile of the whole project, excluding common generated/vendor dirs.
    py_files = []
    for p in ROOT.rglob("*.py"):
        parts = set(p.parts)
        if any(x in parts for x in {".git", ".venv", "venv", "__pycache__", "site-packages"}):
            continue
        py_files.append(str(p))
    if py_files:
        compile_result = run([sys.executable, "-m", "py_compile", *py_files], timeout=180)
    else:
        compile_result = {"ok": False, "returncode": -1, "stdout": "", "stderr": "No Python files found"}
    report["checks"]["python_syntax"] = compile_result

    # Run each installed phase verification independently.
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

    # Optional pytest pass if pytest is installed.
    pytest_probe = run([sys.executable, "-c", "import pytest; print(pytest.__version__)"], timeout=20)
    report["checks"]["pytest_available"] = pytest_probe["ok"]
    if pytest_probe["ok"]:
        report["checks"]["pytest"] = run([sys.executable, "-m", "pytest", "-q"], timeout=240)

    # Marker continuity.
    installed = [x["phase"] for x in report["phase_checks"] if x["marker_present"]]
    report["installed_phase_bundles"] = installed

    failed = []
    if not report["checks"]["root_exists"]:
        failed.append("root_exists")
    if not compile_result["ok"]:
        failed.append("python_syntax")
    for x in report["phase_checks"]:
        if x["marker_present"]:
            if not x["verifier_present"]:
                failed.append(f'phase_{x["phase"]}_verifier_missing')
            elif not x["result"]["ok"]:
                failed.append(f'phase_{x["phase"]}_verification_failed')
    if report["checks"].get("pytest_available") and not report["checks"]["pytest"]["ok"]:
        failed.append("pytest")

    report["success"] = not failed
    report["failed_checks"] = failed
    report["status"] = "full_system_check_passed" if not failed else "full_system_check_failed"

    out = ROOT / "FULL_SYSTEM_CHECK_REPORT.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("=" * 64)
    print("COMPANYOS FULL SYSTEM CHECK")
    print("=" * 64)
    print(f'Root: {ROOT}')
    print(f'Installed bundles: {", ".join(installed) if installed else "none detected"}')
    print(f'Python syntax: {"PASS" if compile_result["ok"] else "FAIL"}')
    for x in report["phase_checks"]:
        if not x["marker_present"]:
            print(f'Phase {x["phase"]}: NOT INSTALLED / NO MARKER')
        elif not x["verifier_present"]:
            print(f'Phase {x["phase"]}: FAIL (verifier missing)')
        else:
            print(f'Phase {x["phase"]}: {"PASS" if x["result"]["ok"] else "FAIL"}')
    if report["checks"].get("pytest_available"):
        print(f'Pytest: {"PASS" if report["checks"]["pytest"]["ok"] else "FAIL"}')
    else:
        print("Pytest: SKIPPED (pytest not installed)")
    print("-" * 64)
    print(json.dumps({
        "success": report["success"],
        "status": report["status"],
        "failed_checks": report["failed_checks"],
        "report": str(out),
    }, indent=2))
    sys.exit(0 if report["success"] else 1)

if __name__ == "__main__":
    main()
