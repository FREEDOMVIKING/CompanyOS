from companyos_phase481_496 import MissionQueue
from .closed_loop_cycle import ClosedLoopCycle
from .runtime_state import RuntimeState
from .integration_audit import IntegrationAudit

class PersistentRuntime:
    """717: process one queued mission through the unified closed loop."""

    def __init__(self, root):
        self.queue = MissionQueue(root)
        self.cycle = ClosedLoopCycle(root)
        self.state = RuntimeState(root)
        self.audit = IntegrationAudit(root)

    def run_once(self):
        missions = self.queue.load()
        ready = [m for m in missions if not m.get("blocked_on")]
        if not ready:
            return {
                "success": True,
                "status": "unified_runtime_idle",
                "executed": 0,
                "remaining": len(missions),
            }

        ready.sort(key=lambda m: float(m.get("priority",0.5)), reverse=True)
        mission = ready[0]
        result = self.cycle.run(mission)

        remaining = [m for m in missions if m.get("mission_id") != mission.get("mission_id")]
        next_mission = result.get("next_mission")
        if next_mission and next_mission.get("mission_id"):
            if next_mission["mission_id"] not in {m.get("mission_id") for m in remaining}:
                remaining.append(next_mission)
        self.queue.save(remaining)

        state = self.state.load()
        state["cycles"] = int(state.get("cycles",0)) + 1
        state["last_status"] = result.get("status")
        state["last_venture_id"] = result.get("venture_id")
        state["last_mission_id"] = mission.get("mission_id")
        state["consecutive_failures"] = 0 if result.get("success") else int(state.get("consecutive_failures",0)) + 1
        self.state.save(state)
        self.audit.append("unified_cycle", result)

        return {
            "success": bool(result.get("success")),
            "status": "unified_runtime_cycle_complete",
            "executed": 1,
            "remaining": len(remaining),
            "cycle": result,
            "state": state,
        }
