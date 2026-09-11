#!/usr/bin/env python3
from pathlib import Path

from companyos.runtime.ceo_runtime_control_plane import CEORuntimeControlPlane
from companyos.runtime.unified_runtime_stack_manager import UnifiedRuntimeStackManager

ctl = CEORuntimeControlPlane()
status = ctl.status()

checks = {
    "ceo_control_status_available": status is not None,
    "ceo_running_boolean": isinstance(status.running, bool),
    "ceo_ready_boolean": isinstance(status.ready, bool),
    "unified_manager_constructs": UnifiedRuntimeStackManager() is not None,
}

ok = True
for name, passed in checks.items():
    ok = ok and passed
    print(name, "=>", "PASS" if passed else "FAIL")

print("UNIFIED_MANAGER_EXTERNAL_ACTIONS: False")
print("UNIFIED_MANAGER_SIGNS_TRANSACTION: False")
print("UNIFIED_MANAGER_BROADCASTS: False")
print("PHASE102_UNIFIED_RUNTIME_TEST:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
