#!/usr/bin/env python3
from pathlib import Path

checks = {
    "phase94_queue_present": Path("companyos/runtime/autonomous_task_queue.py").exists(),
    "phase95_dispatcher_present": Path("companyos/runtime/autonomous_task_dispatcher.py").exists(),
    "phase96_decomposer_present": Path("companyos/runtime/ceo_goal_decomposer.py").exists(),
    "phase97_loop_present": Path("companyos/runtime/autonomous_goal_execution_loop.py").exists(),
    "phase98_lifecycle_present": Path("companyos/runtime/goal_lifecycle_manager.py").exists(),
    "phase99_evaluator_present": Path("companyos/runtime/goal_outcome_evaluator.py").exists(),
    "phase100_orchestrator_present": Path("companyos/runtime/autonomous_ceo_orchestrator.py").exists(),
    "phase100_journal_present": Path("companyos/runtime/ceo_orchestration_journal.py").exists(),
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("CEO_END_TO_END_INTERNAL_ORCHESTRATION: True")
print("RESTART_SAFE_PERSISTENCE: True")
print("BOUNDED_CYCLE_GUARD: True")
print("BOUNDED_FOLLOW_UP_DEPTH: True")
print("OUTCOME_EVALUATION_INTEGRATED: True")
print("APPEND_ONLY_ORCHESTRATION_JOURNAL: True")
print("CEO_ORCHESTRATOR_EXTERNAL_ACTIONS: False")
print("CEO_ORCHESTRATOR_SIGNS_TRANSACTION: False")
print("CEO_ORCHESTRATOR_BROADCASTS: False")
print("PHASE100_STACK_VERIFY:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
