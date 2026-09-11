from .problem_signal import ProblemSignalEngine
from .roadmap_engine import ProductRoadmapEngine
from .feature_scoring import FeatureScoringEngine
from .prototype_planner import PrototypePlanner
from .validation_engine import ProductValidationEngine
from .release_planner import ReleasePlanner
from .quality_gate import ProductQualityGate
from .adoption_engine import AdoptionEngine
from .product_analytics import ProductAnalyticsEngine
from .innovation_portfolio import InnovationPortfolioEngine
from .authority_boundary import ProductAuthorityBoundary
from .state_store import ProductOpsState
from .audit import ProductOpsAudit

class CEOProductOpsController:
    def __init__(self,root):
        self.state=ProductOpsState(root)
        self.audit=ProductOpsAudit(root)

    def run(self, problem_signals=None, initiatives=None, features=None, concept=None,
            experiments=None, release=None, quality_signals=None, cohorts=None,
            product_metrics=None, innovation_bets=None, innovation_budget=0, actions=None):
        ranked_problems=ProblemSignalEngine().rank(problem_signals or [])
        roadmap=ProductRoadmapEngine().prioritize(initiatives or [])
        scored_features=FeatureScoringEngine().score(features or [])
        prototype=PrototypePlanner().plan(concept or {})
        validation=ProductValidationEngine().evaluate(experiments or [])
        release_plan=ReleasePlanner().plan(release or {})
        quality=ProductQualityGate().evaluate(quality_signals or {})
        adoption=AdoptionEngine().analyze(cohorts or [])
        analytics=ProductAnalyticsEngine().summarize(product_metrics or {})
        innovation=InnovationPortfolioEngine().allocate(innovation_bets or [],innovation_budget)
        boundaries=[{**a,**ProductAuthorityBoundary().evaluate(a)} for a in (actions or [])]

        result={
            "success":True,
            "status":"autonomous_product_innovation_cycle_complete",
            "ranked_problem_signals":ranked_problems,
            "roadmap":roadmap,
            "feature_scores":scored_features,
            "prototype_plan":prototype,
            "validation":validation,
            "release_plan":release_plan,
            "quality_gate":quality,
            "adoption":adoption,
            "product_analytics":analytics,
            "innovation_portfolio":innovation,
            "authority_boundaries":boundaries
        }
        self.state.save(result)
        self.audit.append("product_innovation_cycle",result)
        return result
