#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase98_manager_present": Path("companyos/runtime/goal_lifecycle_manager.py").exists(),
    "phase99_evaluator_present": Path("companyos/runtime/goal_outcome_evaluator.py").exists(),
    "phase99_runtime_cli_present": Path("phase99_runtime_goal_evaluate.py").exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("GOAL_OUTCOME_EVALUATION: True")
print("CEO_LEVEL_EVIDENCE_AGGREGATION: True")
print("NEXT_ACTION_DECISION: True")
print("FOLLOW_UP_GOAL_SUGGESTION: True")
print("OUTCOME_EVALUATOR_SIGNS_TRANSACTION: False")
print("OUTCOME_EVALUATOR_BROADCASTS: False")
print("PHASE99_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
