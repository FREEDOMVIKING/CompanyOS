from companyos_phase401_416 import CEOVentureBridge

class VentureStage:
    """472: create venture packet after validated GO."""

    def __init__(self):
        self.bridge = CEOVentureBridge()

    def run(self, context=None):
        context = context or {}
        thesis = context.get("thesis") or context.get("top_thesis")
        decision = context.get("decision") or {"decision":"go_to_mvp"}
        validation = {"decision": decision}

        if not thesis:
            return {"success":False,"status":"venture_missing_thesis","stage":"venture","data":{}}

        packet = self.bridge.create_venture(thesis, validation)
        return {
            "success":bool(packet.get("success")),
            "status":packet.get("status","venture_stage_complete"),
            "stage":"venture",
            "data":{"venture_packet":packet,"venture_id":packet.get("venture_id")},
        }
