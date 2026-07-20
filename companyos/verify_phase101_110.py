import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "agents/phase101_mission_control/mission_control.py",
    ROOT / "agents/phase102_goal_decomposer/goal_decomposer.py",
    ROOT / "agents/phase103_persistent_plan_store/plan_store.py",
    ROOT / "agents/phase104_result_handoff/result_handoff.py",
    ROOT / "agents/phase105_replanner/replanner.py",
    ROOT / "agents/phase106_budget_envelope/budget_envelope.py",
    ROOT / "agents/phase107_checkpoint_manager/checkpoint_manager.py",
    ROOT / "agents/phase108_continuous_mission_runner/mission_runner.py",
    ROOT / "agents/phase109_ceo_loop/ceo_loop.py",
    ROOT / "agents/phase110_companyos_mission_core/missionctl.py",
]
upstream = [
    ROOT / "agents/phase100_companyos_core/companyosctl.py",
    ROOT / "agents/phase98_execution_worker/execution_worker.py",
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
    "status": "phase101_110_verification_passed" if not errors else "phase101_110_verification_failed",
    "checks": checks,
    "errors": errors,
}
print(json.dumps(result, indent=2))
raise SystemExit(0 if not errors else 1)
