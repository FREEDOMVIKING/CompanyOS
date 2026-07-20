#!/usr/bin/env python3
import json, tempfile
from pathlib import Path

from companyos_phase237_244 import (
    ProviderWizard, EnvironmentValidator, ConnectionContract,
    MissionSeed, HandoffReadiness, ProviderActivationRuntime
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase244_verify_"))
(root/"scripts").mkdir()
(root/"scripts"/"companyos_coder_adapter.py").write_text("print('adapter')\\n", encoding="utf-8")

template = ProviderWizard(root).write_template()
assert Path(template["path"]).exists()

env = EnvironmentValidator().validate(root)
assert env["checks"]["project_exists"] is True
assert env["checks"]["coder_adapter_exists"] is True

contract = ConnectionContract().validate({
    "files": {"generated_demo/core.py": "x=1\\n"}
})
assert contract["valid"] is True

mission = MissionSeed().create()
assert "internal_health_summary" in mission["required_capabilities"]

handoff = HandoffReadiness().evaluate({
    "phase220_self_build_pipeline": True,
    "phase228_real_coder_loop": True,
    "provider_probe_passed": False,
    "first_real_model_build_passed": False,
    "full_regression_passed": True,
    "rollback_available": True,
    "persistent_runtime": True,
})
assert handoff["ready"] is False
assert "provider_probe_passed" in handoff["missing"]

runtime = ProviderActivationRuntime(root)
status = runtime.status()
assert status["success"] is True

print(json.dumps({
    "success": True,
    "status": "phase237_244_verification_passed",
    "cycle_status": "phase244_provider_activation_runtime_ready",
    "provider_activation_template": True,
    "environment_validation": True,
    "connection_contract_validation": True,
    "first_real_selfbuild_mission_seeded": True,
    "autonomous_handoff_readiness_gate": True,
    "external_coder_currently_configured": False,
    "autonomy_mode": "high"
}, indent=2))
