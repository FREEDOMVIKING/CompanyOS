from .validation_mission_adapter import ValidationMissionAdapter
from .hypothesis_extractor import HypothesisExtractor
from .experiment_planner import ExperimentPlanner
from .problem_evidence_score import ProblemEvidenceScore
from .pricing_validation import PricingValidation
from .alternative_comparison import AlternativeComparison
from .false_positive_guard import FalsePositiveGuard
from .contradiction_handler import ContradictionHandler
from .validation_confidence import ValidationConfidence
from .decision_threshold import DecisionThreshold
from .revalidation_policy import RevalidationPolicy
from .validation_state import ValidationState
from .validation_audit import ValidationAudit
from .build_promotion_bridge import BuildPromotionBridge

class CEOValidationRuntimeBridge:
    """856: end-to-end validation decision engine."""
    def __init__(self,root):
        self.root=root
        self.state=ValidationState(root)
        self.audit=ValidationAudit(root)

    def run(self,mission):
        adapted=ValidationMissionAdapter().adapt(mission)
        packet=adapted["research_packet"]
        hypotheses=HypothesisExtractor().extract(adapted)
        experiments=ExperimentPlanner().plan(hypotheses)

        problem=ProblemEvidenceScore().score(packet)
        pricing=PricingValidation().score(packet)
        alternatives=AlternativeComparison().evaluate(packet)
        false_guard=FalsePositiveGuard().evaluate(packet)
        contradictions=ContradictionHandler().evaluate(packet)

        confidence=ValidationConfidence().score(
            adapted["research_confidence"],
            problem,
            pricing,
            contradictions["penalty"],
            false_guard["passed"],
        )

        decision=DecisionThreshold().decide(
            confidence,
            false_guard["passed"],
            contradictions["resolved"],
        )
        revalidation=RevalidationPolicy().next(
            decision["decision"],
            adapted["attempts"],
        )

        result={
            "success":True,
            "status":"autonomous_validation_complete",
            "venture_id":adapted["venture_id"],
            "hypotheses":hypotheses,
            "experiments":experiments,
            "scores":{
                "research_confidence":adapted["research_confidence"],
                "problem_evidence":problem,
                "pricing_validation":pricing,
                "validation_confidence":confidence,
            },
            "alternatives":alternatives,
            "false_positive_guard":false_guard,
            "contradictions":contradictions,
            "decision":decision["decision"],
            "decision_reason":decision["reason"],
            "revalidation":revalidation,
        }

        result["next_mission"]=BuildPromotionBridge().build(adapted,result)

        self.state.save(adapted["venture_id"] or adapted["mission_id"],result)
        self.audit.append(result)
        return result
