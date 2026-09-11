#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path

from companyos_phase261_268 import (
    HealthObserver,
    ImprovementPlanner,
    CapabilityMapper,
    ImprovementMission,
    VerificationPolicy,
    LearningRecorder,
    ContinuousImprovementRuntime,
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase268_verify_"))
(root/"tests").mkdir()
(root/".companyos_runtime").mkdir()

obs = HealthObserver(root).observe()
assert obs["signals"]["tests_dir_exists"] is True

proposal = ImprovementPlanner().propose(obs)
assert proposal["internal_only"] is True

mapped = CapabilityMapper().map(proposal)
assert mapped["module_name"].startswith("generated_")

mission = ImprovementMission().create(mapped)
assert "No external actions" in mission["requirements"]
assert "No financial actions" in mission["requirements"]

assert VerificationPolicy().evaluate({"success":False})["approved"] is False
assert VerificationPolicy().evaluate({
    "success":True,
    "regression":{"success":True},
    "registered":{"verified":True},
})["approved"] is True

recorder = LearningRecorder(root)
recorder.record(proposal, mission, {"success":True}, {"approved":True})
assert recorder.path.exists()

status = ContinuousImprovementRuntime(root).status()
assert status["success"] is True
assert status["autonomous_improvement_loop_connected"] is True

print(json.dumps({
    "success": True,
    "status": "phase261_268_verification_passed",
    "cycle_status": "phase268_continuous_improvement_runtime_ready",
    "health_observation": True,
    "autonomous_improvement_planning": True,
    "capability_mapping": True,
    "internal_only_selfbuild_missions": True,
    "verification_before_promotion": True,
    "learning_recording": True,
    "continuous_improvement_loop_connected": True,
    "autonomy_mode": "high"
}, indent=2))
