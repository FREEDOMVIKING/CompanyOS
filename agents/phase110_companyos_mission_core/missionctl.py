import json
import sys

from agents.phase100_companyos_core.companyosctl import dashboard as core_dashboard
from agents.phase101_mission_control.mission_control import create_mission, status as mission_status
from agents.phase103_persistent_plan_store.plan_store import status as plan_status
from agents.phase107_checkpoint_manager.checkpoint_manager import status as checkpoint_status
from agents.phase109_ceo_loop.ceo_loop import run_cycle, status as loop_status

def output(data):
    print(json.dumps(data, indent=2))

def dashboard():
    return {
        "success": True,
        "status": "phase110_companyos_mission_core_dashboard",
        "core": core_dashboard(),
        "missions": mission_status(),
        "plans": plan_status(),
        "checkpoints": checkpoint_status(),
        "ceo_loop": loop_status(),
    }

def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "dashboard"

    if cmd in {"dashboard", "status"}:
        result = dashboard()
    elif cmd == "create-demo-mission":
        result = create_mission(
            "Autonomous Business Discovery",
            "Find, validate, and internally develop a viable AI-powered business opportunity.",
            90,
        )
    elif cmd == "cycle":
        result = run_cycle()
    else:
        result = {
            "success": False,
            "status": "unknown_command",
            "available_commands": ["dashboard", "create-demo-mission", "cycle"],
        }

    output(result)
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
