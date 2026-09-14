from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path.home() / "companyos"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.runtime.launch_health_snapshot import LaunchHealthSnapshot
from companyos.runtime.launch_readiness import LaunchReadinessAudit
from companyos.runtime.launch_runtime import CompanyOSLaunchRuntime


def show(label, value):
    print(f"===== {label} =====")
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def main():
    runtime = CompanyOSLaunchRuntime(ROOT)

    started = runtime.start()
    show("START", started)
    if not started.get("ok"):
        raise SystemExit(20)

    snapshot = LaunchHealthSnapshot(ROOT).build()
    show("SNAPSHOT", snapshot)
    if not snapshot["runtime"]["continuous_runtime"]["healthy"]:
        raise SystemExit(21)

    audit = LaunchReadinessAudit(ROOT).run()
    show("AUDIT", audit)
    if not audit.get("ready"):
        raise SystemExit(22)

    print("COMPANYOS_LAUNCH_STACK_VALIDATION=PASS")


if __name__ == "__main__":
    main()
