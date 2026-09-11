#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.executionops import CapabilityDiscovery, ExecutionReceiptStore, ExecutionVerifier, ExecutionOpsStatus

root = Path(tempfile.mkdtemp())
(root/"coding_agent.py").write_text("def execute(payload): return {'success':True,'status':'completed','output':'ok'}\n")

d = CapabilityDiscovery(root).discover()
assert "coding" in d

v = ExecutionVerifier().verify({"success":True,"status":"completed","output":"ok"})
assert v["passed"] is True

store = ExecutionReceiptStore(root)
store.append({"capability":"coding","verification":{"passed":True}})
assert len(store.recent()) == 1

assert ExecutionOpsStatus().status()["status"] == "phase34000_real_capability_execution_and_receipts_ready"

print(json.dumps({
    "success":True,
    "status":"phase32001_34000_verification_passed",
    "cycle_status":"phase34000_real_capability_execution_and_receipts_ready"
}, indent=2))
