import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required = [
    ROOT / "agents/phase60_watchdog_supervisor/watchdog_supervisor.py",
    ROOT / "agents/phase61_health_monitor/health_monitor.py",
    ROOT / "agents/phase62_recovery_journal/recovery_journal.py",
    ROOT / "agents/phase63_safe_scheduler/safe_scheduler.py",
    ROOT / "agents/phase64_operator_control/operatorctl.py",
]

errors = []
checks = []

for path in required:
    exists = path.exists()
    checks.append({"check": f"file:{path.relative_to(ROOT)}", "passed": exists})
    if not exists:
        errors.append(f"Missing {path}")
        continue
    try:
        py_compile.compile(str(path), doraise=True)
        checks.append({"check": f"compile:{path.relative_to(ROOT)}", "passed": True})
    except Exception as exc:
        checks.append({"check": f"compile:{path.relative_to(ROOT)}", "passed": False})
        errors.append(f"Compile failure {path.name}: {exc}")

# Upstream compatibility checks
upstream = [
    ROOT / "agents/phase58_persistent_runtime/runtime_manager.py",
    ROOT / "agents/phase59_runtime_watchdog/runtime_watchdog.py",
]
for path in upstream:
    ok = path.exists()
    checks.append({"check": f"upstream:{path.relative_to(ROOT)}", "passed": ok})
    if not ok:
        errors.append(f"Missing upstream dependency: {path}")

result = {
    "success": len(errors) == 0,
    "status": "phase60_64_verification_passed" if not errors else "phase60_64_verification_failed",
    "checks": checks,
    "errors": errors,
}

print(json.dumps(result, indent=2))
raise SystemExit(0 if not errors else 1)
