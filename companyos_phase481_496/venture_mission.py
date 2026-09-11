from companyos_phase401_416 import CEOVentureBridge

class VentureMission:
    """490: venture creation mission."""

    def __init__(self):
        self.bridge = CEOVentureBridge()

    def run(self, context=None):
        context = context or {}
        thesis = context.get("thesis") or context.get("top_thesis")
        decision = context.get("decision")

        if not thesis or not decision:
            return {"success":False,"status":"venture_mission_missing_context","mission_type":"venture","data":{}}

        packet = self.bridge.create_venture(thesis, {"decision":decision})
        return {
            "success":bool(packet.get("success")),
            "status":packet.get("status","venture_mission_complete"),
            "mission_type":"venture",
            "data":{"venture_packet":packet},
        }
