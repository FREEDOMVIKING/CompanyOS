class ExperimentLoop:
    """191: run bounded internal experiment state transitions."""
    def next(self,experiment):
        stage=experiment.get("stage","design")
        stages={"design":"execute_internal","execute_internal":"measure","measure":"learn","learn":"iterate"}
        return {**experiment,"stage":stages.get(stage,"iterate"),"autonomous":True,
                "external_action_taken":False,"financial_action_taken":False}
