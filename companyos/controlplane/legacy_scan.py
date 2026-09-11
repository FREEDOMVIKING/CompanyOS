from datetime import datetime, timezone
from pathlib import Path
import ast
import json
from .config import companyos_home
from .storage import atomic_write_json

def scan() -> dict:
    home = companyos_home()
    tests_dir = home / "tests"
    findings = []
    if tests_dir.exists():
        for path in sorted(tests_dir.glob("test_*.py")):
            status = "parse_ok"
            error = None
            try:
                ast.parse(path.read_text(errors="replace"))
            except Exception as exc:
                status = "parse_error"
                error = f"{type(exc).__name__}: {exc}"
            findings.append({"file": str(path), "status": status, "error": error})
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "historical_tests_directory": str(tests_dir),
        "historical_test_count": len(findings),
        "parse_error_count": sum(1 for f in findings if f["status"] == "parse_error"),
        "policy": "Historical tests are reported but not executed by active bundle installers.",
        "findings": findings,
    }
    out = home / "legacy_test_reports" / "latest_legacy_test_scan.json"
    atomic_write_json(out, report)
    print(json.dumps({
        "legacy_test_scan": "complete",
        "historical_test_count": report["historical_test_count"],
        "parse_error_count": report["parse_error_count"],
        "report": str(out),
    }, indent=2))
    return report

if __name__ == "__main__":
    scan()
