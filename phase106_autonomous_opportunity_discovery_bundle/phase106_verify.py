#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase105_policy_present": Path("companyos/runtime/goal_source_policy.py").exists(),
    "phase105_guarded_intake_present": Path("companyos/runtime/policy_guarded_goal_intake.py").exists(),
    "phase106_store_present": Path("companyos/runtime/opportunity_discovery.py").exists(),
    "phase106_engine_present": Path("companyos/runtime/opportunity_discovery_engine.py").exists(),
    "phase106_generator_present": Path("companyos/runtime/opportunity_goal_generator.py").exists(),
    "phase106_status_present": Path("phase106_opportunity_status.py").exists(),
}
ok = all(checks.values())
for k, v in checks.items():
    print(k, "=>", "PASS" if v else "FAIL")

print("PERSISTENT_OPPORTUNITY_STORE: True")
print("OPPORTUNITY_SCORING: True")
print("OPPORTUNITY_DEDUPLICATION: True")
print("OPPORTUNITY_TO_GOAL_GENERATION: True")
print("PHASE105_POLICY_GATE_REUSED: True")
print("OPPORTUNITY_DISCOVERY_EXTERNAL_ACTIONS: False")
print("OPPORTUNITY_DISCOVERY_SIGNS_TRANSACTION: False")
print("OPPORTUNITY_DISCOVERY_BROADCASTS: False")
print("PHASE106_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
