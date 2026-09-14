from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path.home() / "companyos"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from companyos.runtime.runtime_control import UnifiedRuntimeControl


def dump(label, value):
    print(f"===== {label} =====")
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def main():
    ctl = UnifiedRuntimeControl()

    ctl.stop(wait_seconds=5)
    ctl.stop_path.unlink(missing_ok=True)

    started = ctl.start(wait_seconds=15)
    dump("START", started)
    if not started.get("ok"):
        raise SystemExit(10)

    health = ctl.health(stale_after_seconds=45)
    dump("HEALTH", health)
    if not health.get("healthy"):
        raise SystemExit(11)

    first_pid = health.get("supervisor_pid")
    second = ctl.start(wait_seconds=2)
    dump("DUPLICATE START", second)
    second_pid = (second.get("health") or {}).get("supervisor_pid")
    if second.get("action") != "already_running":
        raise SystemExit(12)
    if first_pid != second_pid:
        raise SystemExit(13)

    stopped = ctl.stop(wait_seconds=15)
    dump("STOP", stopped)
    if not stopped.get("ok"):
        raise SystemExit(14)

    time.sleep(1)
    final = ctl.status()
    dump("FINAL", final)
    if final.get("supervisor_alive"):
        raise SystemExit(15)

    print("COMPANYOS_CONTINUOUS_VALIDATION=PASS")


if __name__ == "__main__":
    main()
