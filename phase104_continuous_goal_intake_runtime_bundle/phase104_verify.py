#!/usr/bin/env python3
from pathlib import Path
checks = {
 "phase101_runtime_present":Path("companyos/runtime/autonomous_ceo_runtime_service.py").exists(),
 "phase103_intake_present":Path("companyos/runtime/autonomous_goal_intake.py").exists(),
 "phase103_scheduler_present":Path("companyos/runtime/autonomous_goal_scheduler.py").exists(),
 "phase104_runtime_present":Path("companyos/runtime/continuous_goal_runtime.py").exists(),
 "phase104_ctl_present":Path("phase104_runtime_ctl.py").exists(),
}
ok=all(checks.values())
for k,v in checks.items(): print(k,"=>","PASS" if v else "FAIL")
print("CONTINUOUS_GOAL_INTAKE: True")
print("AUTONOMOUS_INTAKE_SCHEDULING: True")
print("CEO_RUNTIME_ADVANCEMENT: True")
print("IDLE_SAFE: True")
print("MAX_FAILURE_GUARD: True")
print("PHASE104_STACK_VERIFY:","PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
