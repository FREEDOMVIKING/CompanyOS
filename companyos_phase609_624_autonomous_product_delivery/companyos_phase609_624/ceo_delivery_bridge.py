from .product_delivery_manager import ProductDeliveryManager
from .build_acceptance import BuildAcceptance
from .qa_gate import QAGate
from .release_candidate import ReleaseCandidate
from .deployment_readiness import DeploymentReadiness
from .outcome_capture import OutcomeCapture
from .delivery_feedback import DeliveryFeedback

class CEODeliveryBridge:
    """623: CEO-facing product delivery and outcome bridge."""

    def prepare(self, packet):
        return ProductDeliveryManager().prepare(packet)

    def review_build(self, venture_id, build_result, qa_evidence):
        acceptance = BuildAcceptance().evaluate(build_result)
        qa = QAGate().evaluate(qa_evidence)
        rc = ReleaseCandidate().create(venture_id, qa, build_result.get("artifacts",[]))
        readiness = DeploymentReadiness().evaluate({
            **qa_evidence,
            "release_candidate_ready":rc["release_candidate_ready"],
        })
        return {
            "success":True,
            "status":"delivery_review_ready",
            "build_acceptance":acceptance,
            "qa":qa,
            "release_candidate":rc,
            "deployment_readiness":readiness,
        }

    def outcome_feedback(self, payload):
        outcome = OutcomeCapture().capture(payload)
        return DeliveryFeedback().build(outcome)
