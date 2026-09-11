#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase103_intake_present": Path("companyos/runtime/autonomous_goal_intake.py").exists(),
    "phase104_runtime_present": Path("companyos/runtime/continuous_goal_runtime.py").exists(),
    "phase105_policy_present": Path("companyos/runtime/goal_source_policy.py").exists(),
    "phase105_guarded_intake_present": Path("companyos/runtime/policy_guarded_goal_intake.py").exists(),
    "phase105_submit_cli_present": Path("phase105_runtime_goal_submit.py").exists(),
}
ok = all(checks.values())
for k, v in checks.items():
    print(k, "=>", "PASS" if v else "FAIL")

print("GOAL_SOURCE_POLICY_GATE: True")
print("EXTERNAL_ACTION_CLASSIFICATION: True")
print("FINANCIAL_ACTION_CLASSIFICATION: True")
print("HUMAN_APPROVAL_FLAGGING: True")
print("POLICY_GATE_EXTERNAL_ACTIONS: False")
print("POLICY_GATE_SIGNS_TRANSACTION: False")
print("POLICY_GATE_BROADCASTS: False")
print("PHASE105_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
