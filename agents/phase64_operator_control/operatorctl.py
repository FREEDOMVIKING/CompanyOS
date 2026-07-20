import json
import sys

from agents.phase58_persistent_runtime.runtime_manager import (
    status as runtime_status,
    start as runtime_start,
    stop as runtime_stop,
)
from agents.phase59_runtime_watchdog.runtime_watchdog import watchdog_check
from agents.phase61_health_monitor.health_monitor import health_check
from agents.phase62_recovery_journal.recovery_journal import record as journal_record, status as journal_status
from agents.phase63_safe_scheduler.safe_scheduler import status as scheduler_status, disable as scheduler_disable

def output(data):
    print(json.dumps(data, indent=2))

def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "status"

    if cmd == "status":
        output({
            "success": True,
            "status": "phase64_operator_status",
            "runtime": runtime_status(),
            "health": health_check(),
            "scheduler": scheduler_status(),
            "journal": journal_status(),
        })
        return 0

    if cmd == "start":
        result = runtime_start()
        journal_record("operator_start", {"result": result.get("status"), "pid": result.get("pid")})
        output(result)
        return 0 if result.get("success") else 1

    if cmd == "stop":
        result = runtime_stop()
        journal_record("operator_stop", {"result": result.get("status"), "pid": result.get("pid")})
        output(result)
        return 0 if result.get("success") else 1

    if cmd == "watchdog":
        result = watchdog_check(auto_restart=True)
        journal_record("watchdog_check", {"result": result.get("status")})
        output(result)
        return 0 if result.get("success") else 1

    if cmd == "health":
        result = health_check()
        output(result)
        return 0 if result.get("healthy") else 2

    if cmd == "scheduler-off":
        output(scheduler_disable())
        return 0

    output({
        "success": False,
        "status": "unknown_command",
        "available_commands": [
            "status", "start", "stop", "watchdog", "health", "scheduler-off"
        ],
    })
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
