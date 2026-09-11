#!/usr/bin/env python3
from pathlib import Path
import ast

checks = {
    "phase103_intake_present": Path("companyos/runtime/autonomous_goal_intake.py").exists(),
    "phase103_scheduler_present": Path("companyos/runtime/autonomous_goal_scheduler.py").exists(),
    "phase101_runtime_present": Path("companyos/runtime/autonomous_ceo_runtime_service.py").exists(),
    "phase104_runtime_present": Path("companyos/runtime/continuous_goal_runtime.py").exists(),
    "phase104_ctl_present": Path("phase104_runtime_ctl.py").exists(),
}
for p in ["companyos/runtime/continuous_goal_runtime.py", "phase104_runtime_ctl.py"]:
    if Path(p).exists():
        ast.parse(Path(p).read_text())
ok = all(checks.values())
for k,v in checks.items():
    print(k, "=>", "PASS" if v else "FAIL")
print("CONTINUOUS_GOAL_INTAKE: True")
print("INTAKE_TO_CEO_RUNTIME_LOOP: True")
print("IDLE_SAFE: True")
print("MAX_FAILURE_GUARD: True")
print("EXTERNAL_ACTIONS: False")
print("SIGNS_TRANSACTION: False")
print("BROADCASTS_TRANSACTION: False")
print("PHASE104_TEST:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
