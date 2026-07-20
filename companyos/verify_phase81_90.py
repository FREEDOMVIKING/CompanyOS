import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "agents/phase81_delegation_router/delegation_router.py",
    ROOT / "agents/phase82_specialist_registry/specialist_registry.py",
    ROOT / "agents/phase83_task_graph/task_graph.py",
    ROOT / "agents/phase84_execution_workspace/execution_workspace.py",
    ROOT / "agents/phase85_resource_planner/resource_planner.py",
    ROOT / "agents/phase86_outcome_evaluator/outcome_evaluator.py",
    ROOT / "agents/phase87_failure_recovery/failure_recovery.py",
    ROOT / "agents/phase88_portfolio_prioritizer/portfolio_prioritizer.py",
    ROOT / "agents/phase89_ceo_cycle_engine/ceo_cycle_engine.py",
    ROOT / "agents/phase90_autonomy_control_plane/autonomyctl.py",
]
upstream = [
    ROOT / "agents/phase80_venture_orchestrator/venture_orchestrator.py",
    ROOT / "agents/phase67_execution_policy/execution_policy.py",
]

checks, errors = [], []
for path in required:
    ok = path.exists()
    checks.append({"check": f"file:{path.relative_to(ROOT)}", "passed": ok})
    if not ok:
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
    "status": "phase81_90_verification_passed" if not errors else "phase81_90_verification_failed",
    "checks": checks,
    "errors": errors,
}
print(json.dumps(result, indent=2))
raise SystemExit(0 if not errors else 1)
