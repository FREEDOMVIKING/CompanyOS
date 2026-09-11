#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.signercompat import SanitizedDiagnostics, SignerCompatibilityValidation, SignerCompatStatus

s = SanitizedDiagnostics().sanitize({
    "private_key":"abc",
    "nested":{"token":"xyz","safe":"ok"}
})
assert s["private_key"] == "***REDACTED***"
assert s["nested"]["token"] == "***REDACTED***"
assert s["nested"]["safe"] == "ok"

root = Path(tempfile.mkdtemp())
r = SignerCompatibilityValidation(root).write(
    {"signer_command_configured":True},
    {"success":True,"status":"compatible_signer_contract_found"}
)
assert r["ready_for_signer_validation_retry"] is True
assert r["ready_for_live"] is False

status = SignerCompatStatus().status()
assert status["broadcast_disabled"] is True
assert status["live_execution_auto_enabled"] is False

print(json.dumps({
    "success":True,
    "status":"phase44001_45000_verification_passed",
    "cycle_status":"phase45000_signer_compatibility_bridge_ready"
}, indent=2))
