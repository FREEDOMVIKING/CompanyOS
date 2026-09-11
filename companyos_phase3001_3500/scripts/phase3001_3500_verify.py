#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.execution import *

root=Path(tempfile.mkdtemp())

pool=PersistentWorkerPool(root)
pool.ensure([{"worker_id":"w1","capabilities":["research"],"reliability":.9}])
assert pool.available("research")
assert JobDispatcher().dispatch([{"capability":"research"}],pool.available())[0]["status"]=="assigned"
wf=WorkflowRuntime().start("x",[{"name":"a"},{"name":"b"}])
assert WorkflowRuntime().advance(wf)["current"]==1
assert VentureSpawner().spawn("idea")["stage"]=="discover"
assert AdaptiveRetryEngine().decide("timeout",0)["retry"] is True
assert DeepRecoveryCoordinator().plan([{"kind":"worker_crash"}])[0]["recovery_action"]=="requeue_job_and_restart_worker"
assert BackpressureController().evaluate(100,2)["throttle"] is True
assert ExecutionGuardrails().evaluate({"kind":"production_deploy"})["requires_approval"] is True
assert RuntimeStatus().status()["status"]=="phase3500_autonomous_runtime_execution_fabric_ready"

print(json.dumps({
    "success":True,
    "status":"phase3001_3500_verification_passed",
    "cycle_status":"phase3500_autonomous_runtime_execution_fabric_ready"
},indent=2))
