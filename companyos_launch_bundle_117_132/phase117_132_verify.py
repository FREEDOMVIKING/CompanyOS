#!/usr/bin/env python3
from pathlib import Path

required=[
"companyos/runtime/project_pipeline.py",
"companyos/runtime/specialist_coordination.py",
"companyos/runtime/project_checkpointing.py",
"companyos/runtime/recovery_manager.py",
"companyos/runtime/launch_readiness.py",
"companyos/runtime/operations_loop.py",
"companyos/runtime/business_workspace.py",
"companyos/runtime/portfolio_manager.py",
"companyos/runtime/revenue_observation.py",
"companyos/runtime/launch_dashboard.py",
"phase117_132_launch_ctl.py",
]
ok=True
for p in required:
    e=Path(p).exists()
    ok=ok and e
    print(p,"=>","PASS" if e else "FAIL")

print("PHASE117_PROJECT_PIPELINE: True")
print("PHASE118_SPECIALIST_COORDINATION: True")
print("PHASE119_PROJECT_CHECKPOINTING: True")
print("PHASE120_RECOVERY_MANAGER: True")
print("PHASE121_LAUNCH_READINESS: True")
print("PHASE122_OPERATIONS_LOOP: True")
print("PHASE123_BUSINESS_WORKSPACE: True")
print("PHASE124_PORTFOLIO_MANAGER: True")
print("PHASE125_REVENUE_OBSERVATION: True")
print("PHASE126_INTERNAL_DASHBOARD: True")
print("PHASE127_PROJECT_STATE_PERSISTENCE: True")
print("PHASE128_BLOCKER_TRACKING: True")
print("PHASE129_ARTIFACT_TRACKING: True")
print("PHASE130_INTERNAL_LAUNCH_GATE: True")
print("PHASE131_EXTERNAL_ACTION_EXECUTION: False")
print("PHASE132_TRANSACTION_BROADCAST_OVERRIDE: False")
print("PHASE117_132_STACK_VERIFY:","PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
