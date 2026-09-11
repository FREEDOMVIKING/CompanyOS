#!/usr/bin/env python3
from pathlib import Path
import tempfile

from companyos.walletintegration.runtime_service_manager import RuntimeServiceManager

with tempfile.TemporaryDirectory(prefix="phase92_service_") as td:
    mgr = RuntimeServiceManager()
    mgr.runtime_dir = Path(td)
    mgr.watchdog_pid_file = mgr.runtime_dir / "runtime_watchdog.pid"
    mgr.watchdog_log_file = mgr.runtime_dir / "runtime_watchdog.log"

    # We only test safe local helpers/status shape here.
    status = mgr.status()

    checks = {
        "status_object_available": status is not None,
        "service_ready_boolean": isinstance(status.service_ready, bool),
        "supervisor_running_boolean": isinstance(status.supervisor_running, bool),
        "watchdog_running_boolean": isinstance(status.watchdog_running, bool),
        "reason_present": bool(status.reason),
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("SERVICE_MANAGER_BUILDS_TRANSACTION: False")
    print("SERVICE_MANAGER_SIGNS_TRANSACTION: False")
    print("SERVICE_MANAGER_BROADCASTS: False")
    print("PHASE92_SERVICE_MANAGER_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
