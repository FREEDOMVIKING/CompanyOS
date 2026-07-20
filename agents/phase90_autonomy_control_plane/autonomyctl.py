import json
import sys

from agents.phase80_venture_orchestrator.venture_orchestrator import dashboard as venture_dashboard
from agents.phase89_ceo_cycle_engine.ceo_cycle_engine import run_cycle, status as cycle_status
from agents.phase82_specialist_registry.specialist_registry import status as specialist_status
from agents.phase84_execution_workspace.execution_workspace import status as workspace_status
from agents.phase87_failure_recovery.failure_recovery import status as recovery_status
from agents.phase67_execution_policy.execution_policy import status as policy_status

def output(data):
    print(json.dumps(data, indent=2))

def dashboard():
    return {
        "success": True,
        "status": "phase90_autonomy_control_plane",
        "venture_system": venture_dashboard(),
        "ceo_cycle": cycle_status(),
        "specialists": specialist_status(),
        "workspaces": workspace_status(),
        "recovery": recovery_status(),
        "policy": policy_status(),
    }

def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "dashboard"
    if cmd in {"dashboard", "status"}:
        result = dashboard()
    elif cmd == "cycle":
        result = run_cycle()
    else:
        result = {
            "success": False,
            "status": "unknown_command",
            "available_commands": ["dashboard", "cycle"],
        }
    output(result)
    return 0 if result.get("success") else 1

if __name__ == "__main__":
    raise SystemExit(main())
