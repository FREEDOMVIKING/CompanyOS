class ContinuousAutonomyLoop:
    def next_cycle(self, health, decisions, priorities):
        actions=[]
        if not health.get("healthy",False):
            actions.append("repair_unhealthy_systems")
        if decisions.get("action")=="advance":
            actions.append("execute_top_priorities")
        elif decisions.get("action")=="repair_or_replan":
            actions.append("replan")
        else:
            actions.append("collect_evidence")
        actions.extend(["checkpoint_state","consolidate_memory","schedule_next_cycle"])
        return {
            "continue":True,
            "actions":actions,
            "top_priorities":priorities[:5]
        }
