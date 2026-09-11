#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.controlledexec import ControlledExecutionReceipt, PostExecutionLock, ControlledExecutionStatus

root = Path(tempfile.mkdtemp())

r = ControlledExecutionReceipt(root)
row = r.append({"success":True,"status":"test"})
assert row["success"] is True
assert len(r.recent()) == 1

lock = PostExecutionLock(root)
assert lock.status()["locked"] is False
lock.engage("test")
assert lock.status()["locked"] is True
lock.clear()
assert lock.status()["locked"] is False

s = ControlledExecutionStatus().status()
assert s["post_execution_lockout"] is True
assert s["autonomous_live_enabled"] is False
assert s["broadcast_adapter_integration_ready"] is False

print(json.dumps({
    "success":True,
    "status":"phase52001_54000_verification_passed",
    "cycle_status":"phase54000_controlled_execution_orchestrator_ready"
}, indent=2))
