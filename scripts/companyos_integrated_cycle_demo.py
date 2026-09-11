#!/usr/bin/env python3
import json
from pathlib import Path
from companyos.executionops import CapabilityDiscovery
from companyos.integrationops import StageExecutionBridge, IntegratedOperatingCycleExecutor

root = Path.home() / "companyos"
discovered = CapabilityDiscovery(root).discover()

bridge = StageExecutionBridge(root, available_capabilities=set(discovered.keys()))
executor = IntegratedOperatingCycleExecutor(bridge)

payloads = {
    "discover":{"task":"Discover one bounded business opportunity using available internal research capabilities."},
    "research":{"task":"Research and summarize the selected opportunity using available evidence."},
    "select":{"task":"Select the best candidate using expected value and bounded risk."},
    "plan":{"task":"Create an execution plan with milestones and success criteria."},
    "budget":{"task":"Prepare a budget proposal without moving funds."},
    "build":{"task":"Build or update the smallest reversible internal artifact needed for validation."},
    "test":{"task":"Test the artifact and produce evidence."},
    "launch_review":{"task":"Prepare launch review materials only. Do not deploy externally."},
    "operate":{"task":"Prepare internal operating checklist."},
    "customers":{"task":"Prepare internal customer-response workflow only."},
    "revenue":{"task":"Prepare revenue tracking schema and measurement plan."},
    "accounting":{"task":"Prepare internal accounting categorization and reconciliation checklist."},
    "evaluate":{"task":"Evaluate results and identify next best action."},
    "portfolio_decision":{"task":"Recommend scale, continue validation, pivot, or kill."},
    "learn":{"task":"Capture reusable lessons and assumptions."}
}

result = executor.run(payloads, treasury_policy_satisfied=True)
print(json.dumps({
    "success": True,
    "status": "integrated_cycle_demo_complete",
    "discovered_capabilities": discovered,
    "cycle": result
}, indent=2, default=str))
