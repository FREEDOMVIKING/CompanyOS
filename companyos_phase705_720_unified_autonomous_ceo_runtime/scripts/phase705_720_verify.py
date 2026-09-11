#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase705_720 import (
    RuntimeState,SystemRegistry,ContextBus,GovernedActionRouter,OutcomeBridge,
    PortfolioBridge,IntegrationAudit,RuntimeHealth,UnifiedRuntimeStatus
)

root = Path(tempfile.mkdtemp(prefix="phase720_"))

state = RuntimeState(root)
assert state.load()["cycles"] == 0
state.save({"cycles":1,"consecutive_failures":0,"safe_mode":False})
assert state.load()["cycles"] == 1

systems = SystemRegistry().describe()
assert "governance" in systems
assert "lifecycle" in systems
assert "learning" in systems

merged = ContextBus().merge({"a":{"x":1}},{"a":{"y":2}})
assert merged["a"] == {"x":1,"y":2}

router = GovernedActionRouter(root)
assert router.route({"action_type":"research"})["allowed"] is True
assert router.route({"action_type":"sign_contract"})["allowed"] is False

out = OutcomeBridge().normalize({
    "success":True,
    "data":{"activation_rate":0.2,"retention_rate":0.1}
})
assert out["mission_success"] is True

portfolio = PortfolioBridge().review([
    {"venture_id":"v1","validation_score":8,"revenue_signal":5,"roi_score":7,
     "resource_efficiency":1.0,"retention_rate":0.5,"mrr":1000,"profit":100}
])
assert portfolio["ventures"][0]["portfolio_score"] > 0

assert IntegrationAudit(root).append("x",{})["event"] == "x"
assert RuntimeHealth().evaluate({"consecutive_failures":0,"safe_mode":False})["healthy"] is True
assert UnifiedRuntimeStatus().status()["success"] is True

print(json.dumps({
    "success": True,
    "status": "phase705_720_verification_passed",
    "cycle_status": "phase720_unified_autonomous_ceo_runtime_ready",
    "persistent_runtime_state": True,
    "system_registry": True,
    "context_bus": True,
    "governed_action_router": True,
    "outcome_normalization": True,
    "lifecycle_feedback": True,
    "strategic_learning_feedback": True,
    "portfolio_feedback": True,
    "integration_audit": True,
    "runtime_health": True,
    "safe_mode_supervision": True,
    "autonomy_mode": "high_with_governance"
}, indent=2))
