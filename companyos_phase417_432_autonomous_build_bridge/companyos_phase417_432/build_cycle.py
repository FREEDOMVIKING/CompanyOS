class BuildCycle:
    """420: bounded build-cycle state machine."""

    def start(self, packet):
        budget = packet.get("build_budget", {})
        return {
            "venture_id":packet.get("venture_id"),
            "cycle":1,
            "max_cycles":int(budget.get("max_build_cycles",8)),
            "status":"building",
            "completed_tasks":[],
            "failed_tasks":[],
        }

    def can_continue(self, state):
        return state["cycle"] <= state["max_cycles"] and not state["failed_tasks"]
