#!/usr/bin/env python3
import json, tempfile, time
from pathlib import Path
from companyos.livegate import OneShotAuthorization, LiveGateStatus

root = Path(tempfile.mkdtemp())
auth = OneShotAuthorization(root)
created = auth.create(0.01, "DEST", ttl_seconds=60)
token = created["token"]

assert auth.validate(token, 0.005, "DEST")["allowed"] is True
assert auth.validate(token, 0.02, "DEST")["allowed"] is False
assert auth.validate(token, 0.005, "OTHER")["allowed"] is False

auth.consume()
assert auth.validate(token, 0.005, "DEST")["allowed"] is False

status = LiveGateStatus().status()
assert status["autonomous_live_enabled"] is False

print(json.dumps({
    "success":True,
    "status":"phase50001_52000_verification_passed",
    "cycle_status":"phase52000_controlled_live_readiness_gate_ready"
}, indent=2))
