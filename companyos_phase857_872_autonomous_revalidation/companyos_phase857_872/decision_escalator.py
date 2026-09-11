class DecisionEscalator:
    def resolve(self,decision,loop_state,confidence):
        if decision=="GO": return {"final_decision":"GO","action":"promote_to_build"}
        if decision=="KILL": return {"final_decision":"KILL","action":"archive_venture"}
        if not loop_state.get("continue"):
            return {"final_decision":"KILL" if float(confidence)<0.45 else "HUMAN_REVIEW",
                    "action":"archive_venture" if float(confidence)<0.45 else "escalate_review"}
        return {"final_decision":"REVISE","action":"acquire_more_evidence"}
