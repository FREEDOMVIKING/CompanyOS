#!/usr/bin/env python3
import tempfile
from pathlib import Path
from companyos.runtime.launch_controller import CompanyOSLaunchController

with tempfile.TemporaryDirectory() as td:
    c = CompanyOSLaunchController(root=Path(td))
    a = c.practice_start()
    b = c.status()
    d = c.stop()

    checks = {
        "practice_ready": a.get("status") == "practice_mode_ready",
        "practice_no_broadcast": a.get("transaction_broadcasts_allowed_by_practice_controller") is False,
        "internal_autonomy_true": a.get("internal_reversible_autonomy") is True,
        "status_roundtrip": b.get("mode") == "practice",
        "stop_works": d.get("status") == "stopped",
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print(k, "=>", "PASS" if v else "FAIL")
    print("PHASE70_V2_VERIFY:", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)
