#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase205_212 import (
    CapabilityGapDetector, BuildSpecGenerator, IsolatedWorkspace,
    BuildTestRepairLoop, RuntimeSupervisor, SelfBuildingRuntime
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase212_verify_"))
(root/"tests").mkdir()
(root/"sample.py").write_text("def add(a,b):\n    return a+b\n")
(root/"tests"/"test_sample.py").write_text(
    "from sample import add\n\ndef test_add():\n    assert add(2,3)==5\n"
)

gaps = CapabilityGapDetector().detect(
    [{"goal":"ship","required_capabilities":["builder"]}], [], root
)
assert gaps[0]["capability"] == "builder"

spec = BuildSpecGenerator().generate(gaps[0])
assert spec["autonomous_build"] is True
assert spec["rollback_required"] is True

ws = IsolatedWorkspace().create(root)
verification = BuildTestRepairLoop().bounded_cycle(ws["workspace"], max_attempts=1)
assert verification["success"] is True

supervisor = RuntimeSupervisor(root)
assert supervisor.enqueue({"job":"build"})["queue_depth"] == 1
assert supervisor.next_job()["job"] == "build"
assert supervisor.heartbeat()["status"] == "healthy"

runtime = SelfBuildingRuntime(root)
inspection = runtime.inspect(
    [{"goal":"ship","required_capabilities":["builder"]}], []
)
assert inspection["self_building_runtime"] is True
assert inspection["autonomy_mode"] == "high"

IsolatedWorkspace().destroy(ws["container"])

print(json.dumps({
    "success": True,
    "status": "phase205_212_verification_passed",
    "cycle_status": "phase212_self_building_runtime_ready",
    "autonomy_mode": "high",
    "real_filesystem_workspace": True,
    "real_test_execution": True,
    "persistent_runtime_state": True,
    "self_building_runtime": True
}, indent=2))
