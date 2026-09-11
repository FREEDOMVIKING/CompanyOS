#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.liveexec import *

root=Path(tempfile.mkdtemp())
job=ExecutionJob().create("research","internal_research",{"q":"x"},idempotency_key="k1")
assert job["status"]=="queued"
assert RetryTimeoutPolicy().decide("timeout",0)["retry"]
store=IdempotencyStore(root)
store.record("k1",{"ok":1})
assert store.seen("k1")
assert ExecutionRouter().route(job,[{"name":"r","capabilities":["research"]}])["selected"]["name"]=="r"
assert ApprovalExecutionBridge().split([job,ExecutionJob().create("deploy","production_deploy")])["approval_jobs"]
assert LiveExecutionStatus().status()["status"]=="phase8000_live_capability_execution_control_plane_ready"
print(json.dumps({
 "success":True,
 "status":"phase7501_8000_verification_passed",
 "cycle_status":"phase8000_live_capability_execution_control_plane_ready"
},indent=2))
