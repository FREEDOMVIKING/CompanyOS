import json
import sys

from agents.phase64_operator_control.operatorctl import main as phase64_main
from agents.phase65_opportunity_pipeline.opportunity_pipeline import status as opportunity_status
from agents.phase66_portfolio_manager.portfolio_manager import status as portfolio_status
from agents.phase67_execution_policy.execution_policy import status as policy_status
from agents.phase68_business_memory.business_memory import status as memory_status
from agents.phase69_autonomous_planner.autonomous_planner import status as planner_status, build_plan
from agents.phase61_health_monitor.health_monitor import health_check

def output(data):
    print(json.dumps(data, indent=2))

def dashboard():
    return {
        "success": True,
        "status": "phase70_ceo_command_center",
        "health": health_check(),
        "opportunities": opportunity_status(),
        "portfolio": portfolio_status(),
        "execution_policy": policy_status(),
        "business_memory": memory_status(),
        "planner": planner_status(),
    }

def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "dashboard"

    if cmd in {"dashboard", "status"}:
        output(dashboard())
        return 0

    if cmd == "plan":
        output(build_plan())
        return 0

    if cmd in {"start", "stop", "watchdog", "health", "scheduler-off"}:
        # Reuse Phase 64 operator behavior without duplicating runtime logic.
        original = sys.argv[:]
        try:
            sys.argv = [original[0], cmd]
            return phase64_main() or 0
        finally:
            sys.argv = original

    output({
        "success": False,
        "status": "unknown_command",
        "available_commands": [
            "dashboard", "plan", "start", "stop", "watchdog", "health", "scheduler-off"
        ],
    })
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
