import json
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    ROOT / "agents/phase91_persistent_task_queue/task_queue.py",
    ROOT / "agents/phase92_agent_execution_interface/agent_executor.py",
    ROOT / "agents/phase93_interagent_bus/message_bus.py",
    ROOT / "agents/phase94_tool_dispatch/tool_dispatch.py",
    ROOT / "agents/phase95_artifact_store/artifact_store.py",
    ROOT / "agents/phase96_approval_queue/approval_queue.py",
    ROOT / "agents/phase97_audit_log/audit_log.py",
    ROOT / "agents/phase98_execution_worker/execution_worker.py",
    ROOT / "agents/phase99_end_to_end_orchestrator/orchestrator.py",
    ROOT / "agents/phase100_companyos_core/companyosctl.py",
]
upstream = [
    ROOT / "agents/phase90_autonomy_control_plane/autonomyctl.py",
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
    "status": "phase91_100_verification_passed" if not errors else "phase91_100_verification_failed",
    "checks": checks,
    "errors": errors,
}
print(json.dumps(result, indent=2))
raise SystemExit(0 if not errors else 1)
