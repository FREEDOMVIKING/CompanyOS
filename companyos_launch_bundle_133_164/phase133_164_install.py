#!/usr/bin/env python3
from pathlib import Path
import ast, py_compile, shutil, json
from datetime import datetime, timezone

ROOT=Path.home()/"companyos"
BUNDLE=ROOT/"companyos_launch_bundle_133_164"

module_names=[
"business_objective_engine.py","kpi_registry.py","experiment_manager.py","learning_memory.py",
"risk_register.py","resource_planner.py","artifact_registry.py","qa_gate.py",
"release_candidate_manager.py","customer_signal_store.py","support_queue.py","marketing_plan.py",
"sales_pipeline.py","finance_observer.py","budget_guard.py","decision_journal.py",
"strategy_review.py","autonomous_internal_cycle.py","launch_day_gate.py",
]
mapping=[(n, f"companyos/runtime/{n}") for n in module_names] + [
("phase133_164_ctl.py","phase133_164_ctl.py"),
("phase133_164_test.py","phase133_164_test.py"),
]
stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
backups={}
for src_name,dst_name in mapping:
    src=BUNDLE/src_name; dst=ROOT/dst_name
    text=src.read_text()
    ast.parse(text)
    if dst.exists():
        bak=dst.with_name(dst.name+f".phase133_164_backup_{stamp}")
        shutil.copy2(dst,bak); backups[str(dst)]=str(bak)
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(text)
    py_compile.compile(str(dst),doraise=True)

manifest={
"bundle":"133-164",
"internal_business_control_stack":True,
"objective_kpi_experiment_learning":True,
"risk_resource_artifact_qa":True,
"release_customer_support_marketing_sales":True,
"finance_budget_decision_strategy":True,
"autonomous_internal_cycle":True,
"launch_day_gate":True,
"external_action_execution":False,
"transaction_signing_override":False,
"transaction_broadcast_override":False,
"private_key_printed":False,
"backups":backups,
}
(ROOT/"PHASE133_164_LAUNCH_BUNDLE_INSTALLED.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("PHASE133_164_LAUNCH_BUNDLE: INSTALLED")
print("COMPILE_CHECK: PASS")
print("INTERNAL_BUSINESS_CONTROL_STACK: True")
print("AUTONOMOUS_INTERNAL_CYCLE: True")
print("LAUNCH_DAY_GATE: True")
print("EXTERNAL_ACTION_EXECUTION: False")
print("TRANSACTION_SIGNING_OVERRIDE: False")
print("TRANSACTION_BROADCAST_OVERRIDE: False")
print("PRIVATE_KEY_PRINTED: False")
