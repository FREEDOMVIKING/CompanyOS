#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase53_60 import (
    MissionMemory, DecisionLedger, AgentRouter, ApprovalGuard,
    PortfolioManager, HealthSupervisor, SelfImprovementEngine,
    AutonomousCycleEngine,
)

root = Path(__file__).resolve().parents[1]
mem = MissionMemory(root / "state" / "phase53_60_memory.json")
mem.append({"kind": "verification", "ok": True})

assert AgentRouter().route({"category":"research","title":"Find evidence"}) == "research_agent"
assert ApprovalGuard().evaluate({"type":"send_payment"})["allowed"] is False
assert ApprovalGuard().evaluate({"type":"send_payment","explicit_approval":True})["allowed"] is True
assert PortfolioManager().rank([
    {"name":"a","expected_value":100,"confidence":.9,"risk":.2},
    {"name":"b","expected_value":50,"confidence":.5,"risk":.7}
])[0]["name"] == "a"
assert HealthSupervisor().evaluate({"db":True,"queue":True,"worker":False})["status"] in ("healthy","degraded")
assert SelfImprovementEngine().propose({"metric":"conversion","actual":2,"target":4})["auto_apply"] is False

cycle = AutonomousCycleEngine().run({
    "tasks":[{"category":"strategy","title":"Define next move"}],
    "actions":[{"type":"publish_external","irreversible":True}],
    "ventures":[{"name":"x","expected_value":10,"confidence":.8,"risk":.2}],
    "health_checks":{"core":True,"queue":True},
})
assert cycle["success"] is True
assert cycle["external_action_taken"] is False

out = {
    "success": True,
    "status": "phase53_60_verification_passed",
    "memory_records": len(mem.recent(100)),
    "cycle_status": cycle["status"],
    "external_action_taken": cycle["external_action_taken"],
}
print(json.dumps(out, indent=2))
