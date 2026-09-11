class ExecutiveDecisionLoop:
    def run(self, priorities, scorecard, failures=None):
        next_actions=[]
        if failures:
            next_actions.append("run_recovery")
        if float(scorecard.get("overall",0))<0.5:
            next_actions.append("replan_strategy")
        next_actions.append("execute_top_priorities")
        next_actions.append("measure_results")
        next_actions.append("learn_and_update_memory")
        return {"status":"executive_loop_complete","next_actions":next_actions,
                "top_priorities":priorities[:5]}
