import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

required = [
    ROOT / "agents/phase71_evidence_intake/evidence_intake.py",
    ROOT / "agents/phase72_opportunity_scoring/opportunity_scoring.py",
    ROOT / "agents/phase73_business_architect/business_architect.py",
    ROOT / "agents/phase74_mvp_designer/mvp_designer.py",
    ROOT / "agents/phase75_validation_engine/validation_engine.py",
    ROOT / "agents/phase76_revenue_engine/revenue_engine.py",
    ROOT / "agents/phase77_launch_readiness/launch_readiness.py",
    ROOT / "agents/phase78_learning_loop/learning_loop.py",
    ROOT / "agents/phase79_venture_lifecycle/venture_lifecycle.py",
    ROOT / "agents/phase80_venture_orchestrator/venture_orchestrator.py",
]

upstream = [
    ROOT / "agents/phase65_opportunity_pipeline/opportunity_pipeline.py",
    ROOT / "agents/phase70_ceo_command_center/ceoctl.py",
]

checks, errors = [], []

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
    "status": "phase71_80_verification_passed" if not errors else "phase71_80_verification_failed",
    "checks": checks,
    "errors": errors,
}
print(json.dumps(result, indent=2))
raise SystemExit(0 if not errors else 1)
