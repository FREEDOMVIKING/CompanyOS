from companyos_phase385_400 import CEOValidationBridge

class ValidationStage:
    """471: prepare or evaluate validation for the top thesis."""

    def __init__(self):
        self.bridge = CEOValidationBridge()

    def run(self, context=None):
        context = context or {}
        thesis = context.get("top_thesis")
        metrics = context.get("validation_metrics")

        if not thesis:
            return {"success":False,"status":"validation_missing_thesis","stage":"validation","data":{}}

        if metrics:
            evaluated = self.bridge.evaluate(thesis, metrics)
            return {
                "success":True,
                "status":"validation_decision_ready",
                "stage":"validation",
                "data":{
                    "decision":evaluated.get("decision"),
                    "scorecard":evaluated.get("scorecard"),
                    "thesis":thesis,
                }
            }

        plan = self.bridge.prepare(thesis)
        return {
            "success":True,
            "status":"validation_plan_ready",
            "stage":"validation",
            "data":{
                "decision":{"decision":"run_validation"},
                "plan":plan,
                "thesis":thesis,
            }
        }
