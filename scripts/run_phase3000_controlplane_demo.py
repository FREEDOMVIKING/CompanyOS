#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.controlplane import *

root=Path.home()/"companyos"

bus=EventBus(root)
for topic,payload,prio in [
    ("research",{"department":"research","venture_id":"venture_a"},9),
    ("build",{"department":"product","venture_id":"venture_a"},8),
    ("operate",{"department":"operations","venture_id":"venture_b"},7),
    ("growth",{"department":"growth","venture_id":"venture_a"},6),
]:
    bus.publish(topic,payload,prio)

daemon=CEODaemon(root).run_once(["research","product","operations","growth"],max_events=10)

ventures=[
    {"venture_id":"venture_a","stage":"operate","score":.82,"health":"healthy",
     "growth_score":.8,"validation_confidence":.85,"gross_margin":.72,"strategic_fit":.9,"health_score":.95},
    {"venture_id":"venture_b","stage":"operate","score":.2,"health":"healthy",
     "growth_score":.25,"validation_confidence":.6,"gross_margin":.4,"strategic_fit":.5,"health_score":.8},
]
venture_decisions=[VentureLifecycleSupervisor().evaluate(v) for v in ventures]
portfolio=PortfolioAllocator().allocate(ventures,capital=5000,slots=3)

deadlock=DeadlockDetector().detect([
    {"waiter":"product","holder":"research"},
    {"waiter":"research","holder":"product"}
])

health=SelfHealthMonitor().evaluate({
    "queue_backlog":bus.snapshot()["pending"],
    "consecutive_failures":0,
    "heartbeat_fresh":True,
    "memory_corruption":False
})

checkpoint=CheckpointManager(root).save({
    "daemon":daemon["state"],
    "ventures":venture_decisions,
    "portfolio":portfolio,
    "health":health
})
restart=RestartCoordinator().plan(checkpoint,health)

guardrails={
    "internal_analysis":RuntimeGuardrails().evaluate({"kind":"internal_analysis"}),
    "production_deploy":RuntimeGuardrails().evaluate({"kind":"production_deploy"}),
    "bank_transfer":RuntimeGuardrails().evaluate({"kind":"bank_transfer","amount":1500})
}

snapshot=UnifiedControlAPI().snapshot(
    daemon["state"],bus.snapshot(),health,venture_decisions,portfolio
)

print(json.dumps({
    "daemon":daemon,
    "venture_decisions":venture_decisions,
    "portfolio":portfolio,
    "deadlock":deadlock,
    "health":health,
    "checkpoint":checkpoint,
    "restart":restart,
    "guardrails":guardrails,
    "control_snapshot":snapshot
},indent=2,default=str))
