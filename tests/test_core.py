#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def require(path: Path) -> None:
    if not path.exists():
        raise AssertionError(f"Required path missing: {path}")


def test_required_files() -> None:
    require(ROOT / "company_cycle.py")
    require(ROOT / "company_manager.py")
    require(ROOT / "agents")
    require(ROOT / "ceo_memory")


def test_json_memory() -> None:
    for path in (ROOT / "ceo_memory").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def test_company_cycle_syntax() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(ROOT / "company_cycle.py"),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise AssertionError(result.stderr)


if __name__ == "__main__":
    test_required_files()
    test_json_memory()
    test_company_cycle_syntax()
    print("COMPANYOS_CORE_TESTS_PASSED")
