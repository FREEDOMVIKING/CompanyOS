#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos.controlplane import *

root=Path(tempfile.mkdtemp())

bus=EventBus(root)
e=bus.publish("work",{"department":"operations"},5)
assert bus.snapshot()["pending"]==1
assert bus.next()["event_id"]==e["event_id"]

assert VentureLifecycleSupervisor().evaluate({"venture_id":"v","stage":"operate","score":.8,"health":"healthy"})["action"]=="scale"
assert PortfolioAllocator().allocate([{"venture_id":"v","growth_score":.8,"validation_confidence":.8,"gross_margin":.7}],1000,1)
assert BudgetGovernor().evaluate({"amount":100},10000,12)["allowed"] is True
assert ResourceGovernor().allocate([{"owner":"a","resource":"builder","units":1,"priority":1}],1)["allocations"]
assert DeadlockDetector().detect([{"waiter":"a","holder":"b"},{"waiter":"b","holder":"a"}])["deadlocked"] is True
assert SelfHealthMonitor().evaluate({"queue_backlog":1,"consecutive_failures":0,"heartbeat_fresh":True})["healthy"] is True
assert CommandRouter().route("status")["valid"] is True
assert RuntimeGuardrails().evaluate({"kind":"bank_transfer","amount":1000})["requires_approval"] is True
assert RuntimeStatus().status()["status"]=="phase3000_unified_autonomous_company_control_plane_ready"

print(json.dumps({
 "success":True,
 "status":"phase2601_3000_verification_passed",
 "cycle_status":"phase3000_unified_autonomous_company_control_plane_ready"
},indent=2))
