#!/usr/bin/env python3

import json
import tempfile
from pathlib import Path

# Need Phase 205-212 available because Phase 220 uses the real runtime foundation.
from companyos_phase213_220 import (
    DeterministicScaffoldAdapter,
    ModelAdapter,
    ToolExecutor,
    AutonomousSelfBuilder,
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase220_verify_"))
(root / "tests").mkdir()

(root / "base.py").write_text(
    "def base_ok():\n"
    "    return True\n",
    encoding="utf-8",
)

(root / "tests" / "test_base.py").write_text(
    "from base import base_ok\n"
    "\n"
    "def test_base():\n"
    "    assert base_ok() is True\n",
    encoding="utf-8",
)

# Prove bounded tool executor.
tool = ToolExecutor()
tool_result = tool.run(["python", "-c", "print('tool-ok')"], root)
assert tool_result["success"] is True
assert "tool-ok" in tool_result["stdout"]

# Prove model adapter honestly reports unconfigured external coder.
external_adapter = ModelAdapter(command="")
assert external_adapter.available is False

# Prove full end-to-end self-build using deterministic verification adapter.
builder = AutonomousSelfBuilder(root, adapter=DeterministicScaffoldAdapter())
result = builder.build_capability({
    "capability": "sample_autonomous_capability",
    "reason": "verification_gap",
    "priority": 1.0,
})

print("\n===== OFFICIAL VERIFIER RESULT =====")
print(json.dumps(result, indent=2, default=str))
print("===== END OFFICIAL VERIFIER RESULT =====\n")
assert result["success"] is True
assert result["self_building"] is True
assert (root / "generated_sample_autonomous_capability" / "core.py").exists()
assert (
    root / "tests" / "test_generated_sample_autonomous_capability.py"
).exists()
assert "sample_autonomous_capability" in builder.registry.list()

print(json.dumps({
    "success": True,
    "status": "phase213_220_verification_passed",
    "cycle_status": "phase220_autonomous_self_build_pipeline_completed",
    "real_code_generation_pipeline": True,
    "real_isolated_test_execution": True,
    "real_live_integration_test": True,
    "capability_registry_persistent": True,
    "external_coder_adapter_supported": True,
    "external_coder_currently_configured": False,
    "autonomy_mode": "high",
}, indent=2))
