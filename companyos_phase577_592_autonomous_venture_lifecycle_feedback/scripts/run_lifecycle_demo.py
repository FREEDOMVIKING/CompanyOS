#!/usr/bin/env python3
import json
from pathlib import Path
from companyos_phase577_592 import CEOLifecycleBridge

root = Path.home() / "companyos"
bridge = CEOLifecycleBridge(root)

venture = bridge.ensure_venture(
    "Contractor Bid Copilot",
    "estimating_proposals",
    stage="validation",
    evidence={
        "validation_candidate_ready":True,
        "validation_decision":"go_to_mvp",
    },
)

result = bridge.apply_outcome(
    venture["venture_id"],
    {
        "mission_success":True,
        "tests_passed":True,
        "release_candidate_ready":False,
        "activation_rate":0.0,
        "retention_rate":0.0,
        "revenue_signal":0.0,
    },
)

print(json.dumps(result, indent=2, default=str))
print(json.dumps(bridge.portfolio_feedback(), indent=2, default=str))
