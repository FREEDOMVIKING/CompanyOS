#!/usr/bin/env python3
import json, tempfile
from pathlib import Path

from companyos_phase229_236 import (
    ProviderConfig, CoderCommandBuilder, SelfBuildDaemon,
    BuildAudit, HandoffController, ModelConnectedRuntime
)

root = Path(tempfile.mkdtemp(prefix="companyos_phase236_verify_"))
(root/"scripts").mkdir()

cfg = ProviderConfig(root)
saved = cfg.save("custom", "coder-model", "python adapter.py")
assert saved["provider"] == "custom"
assert cfg.load()["model"] == "coder-model"

cmd = CoderCommandBuilder().build(root)
assert "companyos_coder_adapter.py" in cmd

daemon = SelfBuildDaemon(root)
assert daemon.enqueue({"mission":"x"})["depth"] == 1
assert daemon.pop()["mission"] == "x"
assert daemon.beat()["status"] == "idle"

audit = BuildAudit(root)
audit.record("verify", {"ok":True})
assert audit.path.exists()

handoff = HandoffController().evaluate({
    "real_filesystem_workspace": True,
    "real_test_execution": True,
    "live_integration": True,
    "rollback_available": True,
    "coder_connected": False,
    "persistent_runtime": True,
})
assert handoff["ready"] is False
assert handoff["missing"] == ["coder_connected"]

runtime = ModelConnectedRuntime(root)
status = runtime.status()
assert status["success"] is True
assert status["external_coder_configured"] is False

print(json.dumps({
    "success": True,
    "status": "phase229_236_verification_passed",
    "cycle_status": "phase236_model_connection_layer_ready",
    "provider_configuration": True,
    "generic_provider_adapter": True,
    "persistent_selfbuild_queue": True,
    "selfbuild_audit_log": True,
    "autonomous_handoff_gate": True,
    "external_coder_currently_configured": False,
    "autonomy_mode": "high"
}, indent=2))
