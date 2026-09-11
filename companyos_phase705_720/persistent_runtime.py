from companyos_phase481_496 import MissionQueue
from .closed_loop_cycle import ClosedLoopCycle
from .runtime_state import RuntimeState
from .integration_audit import IntegrationAudit
from companyos_phase737_744 import ResilientExecutor

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

        resilience = ResilientExecutor(self.state.path.parent.parent).handle(
            mission, result, current_provider=((mission.get("context") or {}).get("provider_hint") or "github")
        )
        if resilience.get("handled"):
            deferred=resilience.get("mission")
            if deferred and deferred.get("mission_id"):
                remaining.append(deferred)
            self.queue.save(remaining)
            state=self.state.load()
            state["cycles"]=int(state.get("cycles",0))+1
            state["last_status"]=resilience.get("status")
            state["last_venture_id"]=result.get("venture_id")
            state["last_mission_id"]=mission.get("mission_id")
            state["consecutive_failures"]=int(state.get("consecutive_failures",0))
            self.state.save(state)
            audit_payload={"success":True,"status":resilience.get("status"),"transient":True,"resilience":resilience,"original_result":result}
            self.audit.append("unified_cycle_deferred",audit_payload)
            return {"success":True,"status":"unified_runtime_cycle_deferred","executed":1,"remaining":len(remaining),"cycle":audit_payload,"state":state}

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
