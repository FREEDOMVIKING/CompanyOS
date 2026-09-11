#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos.daemonops import *

root=Path(tempfile.mkdtemp())
q=DurableJobQueue(root)
job=q.enqueue("test",{"x":1},9)
assert q.next_job()["job_id"]==job["job_id"]
assert AutonomousScheduler().due([{"kind":"x","every_ticks":2}],4)
assert TriggerRouter().route({"kind":"market_signal"})["department"]=="research"
assert JobLeaseManager().expired({"lease_expiry_tick":2},3)
assert AutonomousRuntimeStatus().status()["status"]=="phase15500_autonomous_daemon_event_runtime_ready"

print(json.dumps({
    "success":True,
    "status":"phase15001_15500_verification_passed",
    "cycle_status":"phase15500_autonomous_daemon_event_runtime_ready"
},indent=2))
