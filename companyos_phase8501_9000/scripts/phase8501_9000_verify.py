#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.liveintegration import *

root=Path(tempfile.mkdtemp())
cert=ConnectorCertification().certify({
    "name":"x","enabled":True,"capabilities":["research"],"health_score":.9,
    "credentials_ready":True,"fallback_ready":True,"receipts_enabled":True})
assert cert["certified"]

pre=LivePreflight().evaluate({
    "connector_certified":True,"credentials_ready":True,"health_ok":True,
    "rollback_ready":True,"audit_ready":True})
assert pre["passed"]

assert RequestSanitizer().sanitize({"api_key":"abc"})["api_key"]=="***REDACTED***"
assert LiveModeGate().evaluate({"kind":"production_deploy"},pre,approval=False)["requires_approval"]
assert ProviderFailover().choose([{"name":"a","enabled":True,"health_score":.9}])["selected"]=="a"
assert LiveIntegrationStatus().status()["status"]=="phase9000_secure_live_integration_runtime_ready"

print(json.dumps({
    "success":True,
    "status":"phase8501_9000_verification_passed",
    "cycle_status":"phase9000_secure_live_integration_runtime_ready"
},indent=2))
