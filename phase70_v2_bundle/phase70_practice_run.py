#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path

# Practice mode is explicit and local to this process.
os.environ["COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION"] = "0"

from companyos.runtime.launch_readiness_audit import LaunchReadinessAudit
from companyos.runtime.health_supervisor import CompanyOSHealthSupervisor
from companyos.runtime.launch_controller import CompanyOSLaunchController

root = Path.home() / "companyos"

audit = LaunchReadinessAudit(root=root).run()
health = CompanyOSHealthSupervisor(root=root).evaluate()
controller = CompanyOSLaunchController(root=root)
state = controller.practice_start()

checks = {
    "audit_ran": audit.get("success") is True,
    "health_ran": health.get("success") is True,
    "practice_mode": state.get("mode") == "practice",
    "live_financial_execution_forced_off": os.getenv("COMPANYOS_ENABLE_LIVE_FINANCIAL_EXECUTION") == "0",
    "practice_controller_allows_broadcasts": state.get("transaction_broadcasts_allowed_by_practice_controller") is True,
    "internal_reversible_autonomy": state.get("internal_reversible_autonomy") is True,
}

# Expected false for broadcast allowance, so invert that check.
checks["practice_controller_allows_broadcasts"] = not checks["practice_controller_allows_broadcasts"]

ok = all(checks.values())

print("===== COMPANYOS PRACTICE RUN =====")
for name, passed in checks.items():
    print(name, "=>", "PASS" if passed else "FAIL")

summary = {
    "success": ok,
    "status": "practice_run_passed" if ok else "practice_run_failed",
    "audit_core_runtime_ready": audit.get("core_runtime_ready"),
    "health": health.get("health"),
    "live_financial_execution": False,
    "transaction_broadcasts_from_practice_controller": False,
    "internal_reversible_autonomy": True,
}
print(json.dumps(summary, indent=2))
print("COMPANYOS_PRACTICE_RUN:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
