#!/usr/bin/env python3
import json
from companyos_phase433_448 import (
    VentureState, ResourceAllocator, PriorityEngine, SpecialistCoordinator,
    FailurePolicy, RetryScheduler, LifecycleManager, PortfolioSnapshot,
    VentureExecutor, ExecutionManager, CEOPortfolioRouter, VentureHealth,
    ExecutionRuntime
)

state = VentureState("v1","Test Venture")
assert state.to_dict()["status"] == "queued"

ventures = [
    {"venture_id":"a","name":"A","priority":0.9,"status":"building","failures":0,
     "metrics":{"validation_score":8},
     "specialist_jobs":[{"id":"T1","task":"spec","depends_on":[]}],
     "completed_task_ids":[]},
    {"venture_id":"b","name":"B","priority":0.4,"status":"queued","failures":0,
     "metrics":{"validation_score":5},
     "specialist_jobs":[{"id":"T1","task":"spec","depends_on":[]}],
     "completed_task_ids":[]},
]

assert len(ResourceAllocator().allocate(ventures,1)["active"]) == 1
assert PriorityEngine().score(ventures[0]) > PriorityEngine().score(ventures[1])
assert SpecialistCoordinator().ready_jobs(ventures[0]["specialist_jobs"],[])
assert FailurePolicy().decide(1,0)["action"] == "retry"
assert RetryScheduler().delay_seconds(2) > RetryScheduler().delay_seconds(0)
assert LifecycleManager().transition("queued","building")["success"] is True
assert PortfolioSnapshot().build(ventures)["venture_count"] == 2
assert VentureHealth().evaluate(ventures[0])["level"] == "healthy"
assert VentureExecutor().next_action(ventures[0])["action"] == "dispatch_jobs"
assert ExecutionManager().manage(ventures,1)["success"] is True
assert CEOPortfolioRouter().route(ventures,1)["ceo_directive"]["fund_attention_to"]
assert ExecutionRuntime().status()["success"] is True

print(json.dumps({
    "success":True,
    "status":"phase433_448_verification_passed",
    "cycle_status":"phase448_persistent_venture_execution_manager_ready",
    "multi_venture_queue":True,
    "resource_allocation":True,
    "priority_engine":True,
    "specialist_coordination":True,
    "failure_retry_policy":True,
    "progress_tracking":True,
    "lifecycle_management":True,
    "portfolio_snapshot":True,
    "ceo_resource_routing":True,
    "autonomy_mode":"high"
}, indent=2))
