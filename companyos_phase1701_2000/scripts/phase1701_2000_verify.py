#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.runtime import *

root=Path(tempfile.mkdtemp())

q=PersistentJobQueue(root)
j=q.enqueue("daily_cycle",{"department":"operations"},7)
assert q.snapshot()["queued"]==1
assert q.next()["job_id"]==j["job_id"]

hb=RuntimeHeartbeat(root).beat("svc",{"ok":True})
assert RuntimeWatchdog().evaluate(hb)["healthy"] is True

assert AutonomousScheduler().plan({"daily":["x"]})
assert CrossVentureResourceScheduler().allocate([{"venture_id":"v1","priority_score":.9,"requested_slots":1}],1)["allocations"]

cp=CheckpointStore(root).save({"x":1})
assert RestartSafeRecovery().recover(cp,{"running":0})["recoverable"] is True
assert RuntimeIncidentManager().classify("rate limit exceeded")["kind"]=="rate_limited"
assert RuntimeStatus().status()["status"]=="phase2000_persistent_autonomous_company_runtime_ready"

print(json.dumps({
    "success":True,
    "status":"phase1701_2000_verification_passed",
    "cycle_status":"phase2000_persistent_autonomous_company_runtime_ready"
},indent=2))
