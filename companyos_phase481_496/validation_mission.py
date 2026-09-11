from companyos_phase385_400 import CEOValidationBridge

class ValidationMission:
    """489: validation mission using stored or supplied evidence metrics."""

    def __init__(self):
        self.bridge = CEOValidationBridge()

    def run(self, context=None):
        context = context or {}
        thesis = context.get("thesis") or context.get("top_thesis")
        metrics = context.get("validation_metrics")

        if not thesis:
            return {"success":False,"status":"validation_mission_missing_thesis","mission_type":"validation","data":{}}

        if not metrics:
            return {
                "success":True,
                "status":"validation_mission_waiting_for_evidence",
                "mission_type":"validation",
                "data":{"plan":self.bridge.prepare(thesis)},
            }

        result = self.bridge.evaluate(thesis, metrics)
        return {
            "success":True,
            "status":"validation_mission_decision_ready",
            "mission_type":"validation",
            "data":result,
        }
