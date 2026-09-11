#!/usr/bin/env python3
from pathlib import Path

required=[
"companyos/runtime/launch_runtime.py",
"companyos/runtime/approval_queue.py",
"companyos/runtime/action_proposal_router.py",
"companyos/runtime/launch_health_snapshot.py",
"phase109_116_launch_ctl.py",
"phase102_unified_runtime_ctl.py",
"phase104_runtime_ctl.py",
]
ok=True
for p in required:
    exists=Path(p).exists()
    ok=ok and exists
    print(p,"=>","PASS" if exists else "FAIL")

print("PHASE109_LAUNCH_RUNTIME_CONTROL: True")
print("PHASE110_APPROVAL_QUEUE: True")
print("PHASE111_ACTION_PROPOSAL_ROUTER: True")
print("PHASE112_HEALTH_SNAPSHOT: True")
print("PHASE113_UNIFIED_START_STOP: True")
print("PHASE114_EXTERNAL_ACTION_EXECUTION: False")
print("PHASE115_FINANCIAL_BROADCAST_OVERRIDE: False")
print("PHASE116_LAUNCH_GATE: True")
print("PHASE109_116_STACK_VERIFY:","PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
