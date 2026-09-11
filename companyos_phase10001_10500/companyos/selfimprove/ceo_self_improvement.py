from .performance_baseline import PerformanceBaseline
from .bottleneck_detector import BottleneckDetector
from .improvement_planner import ImprovementPlanner
from .safe_patch_generator import SafePatchGenerator
from .sandbox_validator import SandboxValidator
from .regression_guard import RegressionGuard
from .canary_controller import CanaryController
from .learning_policy import LearningPolicy
from .knowledge_distiller import KnowledgeDistiller
from .strategy_evolver import StrategyEvolver
from .architecture_review import ArchitectureReview
from .human_boundary import SelfImprovementBoundary
from .state_store import SelfImprovementState
from .audit import SelfImprovementAudit

class CEOSelfImprovementController:
    def __init__(self,root):
        self.state=SelfImprovementState(root)
        self.audit=SelfImprovementAudit(root)

    def run(self, metrics=None, thresholds=None, patch_requests=None, tests=None,
            candidate_metrics=None, events=None, current_strategy=None, modules=None, changes=None):
        baseline=PerformanceBaseline().build(metrics or {})
        bottlenecks=BottleneckDetector().detect(baseline,thresholds or {})
        plan=ImprovementPlanner().plan(bottlenecks)
        proposals=[SafePatchGenerator().propose(
            p.get("component"),p.get("change"),p.get("reversible",True)
        ) for p in (patch_requests or [])]
        validations=[SandboxValidator().validate(p,tests or []) for p in proposals]
        regression=RegressionGuard().compare(baseline,candidate_metrics or baseline)
        canaries=[CanaryController().decide(v,regression) for v in validations]
        knowledge=KnowledgeDistiller().distill(events or [])
        evolved=StrategyEvolver().evolve(current_strategy or {},knowledge)
        architecture=ArchitectureReview().evaluate(modules or [])
        boundaries=[SelfImprovementBoundary().evaluate(c) for c in (changes or [])]
        learning=[LearningPolicy().evaluate(c) for c in (changes or [])]

        result={
            "success":True,
            "status":"self_improving_autonomous_enterprise_cycle_complete",
            "baseline":baseline,
            "bottlenecks":bottlenecks,
            "improvement_plan":plan,
            "patch_proposals":proposals,
            "sandbox_validations":validations,
            "regression_guard":regression,
            "canary_decisions":canaries,
            "knowledge":knowledge,
            "evolved_strategy":evolved,
            "architecture_review":architecture,
            "protected_boundaries":boundaries,
            "learning_policy":learning
        }
        self.state.save(result)
        self.audit.append("self_improvement_cycle",result)
        return result
