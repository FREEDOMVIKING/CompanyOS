#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.daemonops import DurableJobQueue
from companyos.workerops import DurableWorkerPool, WorkerOpsStatus

root=Path(tempfile.mkdtemp())
q=DurableJobQueue(root)
q.enqueue("market_scan",{"scope":"opportunities"},9)
pool=DurableWorkerPool(root)
result=pool.process_one(q,worker_id="verify_worker",tick=1)
assert result["processed"]
assert result["decision"]["action"]=="complete"
assert q.load()[0]["status"]=="complete"
assert WorkerOpsStatus().status()["status"]=="phase16000_durable_worker_execution_queue_drain_ready"

print(json.dumps({
    "success":True,
    "status":"phase15501_16000_verification_passed",
    "cycle_status":"phase16000_durable_worker_execution_queue_drain_ready"
},indent=2))
