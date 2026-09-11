#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.capabilityops import CapabilityRegistry, CredentialReadiness, CapabilityOpsStatus, RealExecutionBridge

root=Path(tempfile.mkdtemp())
registry=CapabilityRegistry().build()
assert "reasoning" in registry
ready=CredentialReadiness().evaluate(registry)
assert "research" in ready

job={"job_id":"verify_job","kind":"research","payload":{"query":"test"}}
result=RealExecutionBridge(root).execute(job,"research")
assert result["success"] is True
assert result["mode"]=="internal_fallback"

status=CapabilityOpsStatus().status()
assert status["status"]=="phase16500_real_capability_execution_layer_ready"

print(json.dumps({
    "success":True,
    "status":"phase16001_16500_verification_passed",
    "cycle_status":"phase16500_real_capability_execution_layer_ready",
    "note":"Real external execution activates only when capability endpoints/credentials are configured."
},indent=2))
