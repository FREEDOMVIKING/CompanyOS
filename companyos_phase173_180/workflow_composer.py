class WorkflowComposer:
    """177: compose reusable internal workflows from available skills."""
    def compose(self, objective, skills):
        selected=[s for s in skills if objective in s.get("supports",[]) or not s.get("supports")]
        return {"objective":objective,"steps":[s.get("name") for s in selected],
                "autonomous_execution":True,"reversible_internal_workflow":True}
