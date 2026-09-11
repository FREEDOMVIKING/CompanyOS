from .venture_orchestrator import VentureOrchestrator

class CEOVentureBridge:
    """415: CEO bridge from validated opportunity to managed venture."""

    def __init__(self):
        self.factory = VentureOrchestrator()

    def create_venture(self, thesis, validation):
        packet = self.factory.prepare(thesis, validation)
        if not packet.get("success"):
            return packet
        return {
            **packet,
            "ceo_directive":"build_bounded_mvp_then_measure",
            "portfolio_state":"incubating",
            "next_gate":"release_candidate_quality_review",
        }
