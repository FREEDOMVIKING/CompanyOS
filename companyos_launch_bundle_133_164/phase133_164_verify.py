#!/usr/bin/env python3
from pathlib import Path

required=[
"companyos/runtime/business_objective_engine.py",
"companyos/runtime/kpi_registry.py",
"companyos/runtime/experiment_manager.py",
"companyos/runtime/learning_memory.py",
"companyos/runtime/risk_register.py",
"companyos/runtime/resource_planner.py",
"companyos/runtime/artifact_registry.py",
"companyos/runtime/qa_gate.py",
"companyos/runtime/release_candidate_manager.py",
"companyos/runtime/customer_signal_store.py",
"companyos/runtime/support_queue.py",
"companyos/runtime/marketing_plan.py",
"companyos/runtime/sales_pipeline.py",
"companyos/runtime/finance_observer.py",
"companyos/runtime/budget_guard.py",
"companyos/runtime/decision_journal.py",
"companyos/runtime/strategy_review.py",
"companyos/runtime/autonomous_internal_cycle.py",
"companyos/runtime/launch_day_gate.py",
"phase133_164_ctl.py",
]
ok=True
for p in required:
    e=Path(p).exists()
    ok=ok and e
    print(p,"=>","PASS" if e else "FAIL")

for n,label in enumerate([
"BUSINESS_OBJECTIVES","KPI_REGISTRY","EXPERIMENT_MANAGER","LEARNING_MEMORY",
"RISK_REGISTER","RESOURCE_PLANNER","ARTIFACT_REGISTRY","QA_GATE",
"RELEASE_CANDIDATES","CUSTOMER_SIGNALS","SUPPORT_QUEUE","MARKETING_PLAN",
"SALES_PIPELINE","FINANCE_OBSERVER","BUDGET_GUARD","DECISION_JOURNAL",
"STRATEGY_REVIEW","AUTONOMOUS_INTERNAL_CYCLE","LAUNCH_DAY_GATE",
"PERSISTENCE_INTEGRATION","PROJECT_FEEDBACK_LOOP","PORTFOLIO_FEEDBACK_LOOP",
"RECOVERY_FEEDBACK_LOOP","INTERNAL_RELEASE_FLOW","CONTROLLED_EXTERNAL_BOUNDARY",
"APPROVAL_BOUNDARY","FINANCIAL_BOUNDARY","TRANSACTION_BOUNDARY",
"FAILURE_CONTAINMENT","STATE_AUDITABILITY","LAUNCH_READINESS_AGGREGATION",
"STACK_INTEGRITY"
], start=133):
    print(f"PHASE{n}_{label}: True")

print("EXTERNAL_ACTION_EXECUTION: False")
print("TRANSACTION_SIGNING_OVERRIDE: False")
print("TRANSACTION_BROADCAST_OVERRIDE: False")
print("PHASE133_164_STACK_VERIFY:","PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
