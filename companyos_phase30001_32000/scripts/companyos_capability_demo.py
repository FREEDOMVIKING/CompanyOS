#!/usr/bin/env python3
import json
from companyos.capabilityops import StageCapabilityRouter, ControlledAutonomyPolicy, RealCapabilityOperatingExecutor

stages = [
    "discover","research","select","plan","budget","build","test","launch_review",
    "operate","customers","revenue","accounting","evaluate","portfolio_decision","learn"
]
available = {
    "research","analysis","ceo","planning","finance","coding","engineering","quality",
    "operations","customer_success","communications","portfolio_review","strategy","memory"
}

rows = RealCapabilityOperatingExecutor(
    StageCapabilityRouter(),
    ControlledAutonomyPolicy()
).build_stage_plan(
    stages,
    available,
    treasury_policy_satisfied=True
)

print(json.dumps({
    "success": True,
    "status": "real_capability_execution_plan_built",
    "stages": rows
}, indent=2))
