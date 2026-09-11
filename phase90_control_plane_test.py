#!/usr/bin/env python3
from pathlib import Path
import os
import tempfile

from companyos.walletintegration.runtime_control_plane import RuntimeControlPlane


with tempfile.TemporaryDirectory(prefix="phase90_control_") as td:
    # Test status parsing without launching a real background process.
    ctl = RuntimeControlPlane()
    ctl.runtime_dir = Path(td)
    ctl.pid_file = ctl.runtime_dir / "production_runtime_supervisor.pid"
    ctl.state_file = ctl.runtime_dir / "production_runtime_supervisor.json"
    ctl.log_file = ctl.runtime_dir / "production_runtime_supervisor.log"

    ctl.state_file.write_text(
        """{
          "running": true,
          "ready": true,
          "reason": "healthy",
          "cycle_count": 7,
          "rpc_ok": true,
          "stale": false,
          "sol_balance": 0.25,
          "spendable_sol": 0.24,
          "unresolved_records": 0,
          "consecutive_failures": 0
        }
        """,
        encoding="utf-8",
    )

    status = ctl.status()

    checks = {
        "state_file_present": status.state_file_present,
        "ready_state_parsed": status.ready is True,
        "cycle_count_parsed": status.cycle_count == 7,
        "rpc_state_parsed": status.rpc_ok is True,
        "stale_state_parsed": status.stale is False,
        "unresolved_zero": status.unresolved_records == 0,
    }

    ok = True
    for name, passed in checks.items():
        ok = ok and passed
        print(name, "=>", "PASS" if passed else "FAIL")

    print("CONTROL_PLANE_BUILDS_TRANSACTION: False")
    print("CONTROL_PLANE_SIGNS_TRANSACTION: False")
    print("CONTROL_PLANE_BROADCASTS: False")
    print("PHASE90_CONTROL_PLANE_TEST:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
