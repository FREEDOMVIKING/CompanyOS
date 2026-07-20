import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required = [
    ROOT / "agents/phase65_opportunity_pipeline/opportunity_pipeline.py",
    ROOT / "agents/phase66_portfolio_manager/portfolio_manager.py",
    ROOT / "agents/phase67_execution_policy/execution_policy.py",
    ROOT / "agents/phase68_business_memory/business_memory.py",
    ROOT / "agents/phase69_autonomous_planner/autonomous_planner.py",
    ROOT / "agents/phase70_ceo_command_center/ceoctl.py",
]

upstream = [
    ROOT / "agents/phase64_operator_control/operatorctl.py",
    ROOT / "agents/phase61_health_monitor/health_monitor.py",
]

checks = []
errors = []

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

for path in upstream:
    ok = path.exists()
    checks.append({"check": f"upstream:{path.relative_to(ROOT)}", "passed": ok})
    if not ok:
        errors.append(f"Missing upstream dependency: {path}")

result = {
    "success": len(errors) == 0,
    "status": "phase65_70_verification_passed" if not errors else "phase65_70_verification_failed",
    "checks": checks,
    "errors": errors,
}
print(json.dumps(result, indent=2))
raise SystemExit(0 if not errors else 1)
