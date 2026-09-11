#!/usr/bin/env python3
import json,tempfile
from pathlib import Path
from companyos_phase721_736 import (
    TestMissionFactory,QueueInjector,CycleProbe,LifecycleProbe,LearningProbe,
    AuditProbe,StateProbe,QueueProbe,IntegrationAssertions,FaultInjector,
    RecoveryProbe,StressPlan,IntegrationReport,HarnessRuntime
)
from companyos_phase577_592 import CEOLifecycleBridge

root=Path(tempfile.mkdtemp(prefix="phase736_"))

mission=TestMissionFactory().create()
assert mission["mission_id"].startswith("mission_test_")
assert mission["context"]["integration_test"] is True

q=QueueInjector(root)
assert q.inject(mission)["inserted"] is True
assert q.inject(mission)["inserted"] is False

assert CycleProbe().inspect({"success":True,"status":"x","executed":1,"remaining":0})["executed"]==1

bridge=CEOLifecycleBridge(root)
v=bridge.ensure_venture("X","integration")
assert LifecycleProbe(root).inspect(v["venture_id"])["present"] is True
assert LearningProbe(root).inspect(v["venture_id"])["venture_id"]==v["venture_id"]
assert isinstance(AuditProbe(root).inspect(),dict)
assert StateProbe(root).inspect()["cycles"]==0
assert QueueProbe(root).inspect()["count"]==1

assert IntegrationAssertions().evaluate(
    {"cycles":0},{"cycles":1,"consecutive_failures":0},
    {"present":True,"stage":"research"},
    {"hypotheses_present":True,"strategy_present":False},
    {"unified_runtime_audit.jsonl":{"exists":True}}
)["passed"] is True

assert FaultInjector().blocked_mission()["blocked_on"]
assert RecoveryProbe().evaluate({"consecutive_failures":0},{"count":1})["recoverable"] is True
assert StressPlan().build(100)["rounds"]==10
assert IntegrationReport().build({"success":True,"status":"ok"})["success"] is True
assert HarnessRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase721_736_verification_passed",
    "cycle_status":"phase736_end_to_end_mission_integration_harness_ready",
    "controlled_test_missions":True,
    "queue_injection":True,
    "runtime_cycle_probing":True,
    "lifecycle_probing":True,
    "learning_probing":True,
    "audit_probing":True,
    "state_probing":True,
    "queue_probing":True,
    "integration_assertions":True,
    "safe_fault_injection":True,
    "recovery_probing":True,
    "bounded_stress_testing":True,
    "integration_reporting":True,
    "autonomy_mode":"high_with_governance"
},indent=2))
