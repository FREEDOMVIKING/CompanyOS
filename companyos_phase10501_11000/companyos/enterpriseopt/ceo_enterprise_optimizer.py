from .enterprise_scorecard import EnterpriseScorecard
from .capital_allocator import EnterpriseCapitalAllocator
from .venture_pruner import VenturePruner
from .strategy_allocator import StrategyAllocator
from .department_capacity import DepartmentCapacityPlanner
from .talent_allocator import TalentAllocator
from .profitability_engine import ProfitabilityEngine
from .portfolio_risk import PortfolioRiskEngine
from .scenario_engine import PortfolioScenarioEngine
from .optimization_loop import EnterpriseOptimizationLoop
from .learning_compounder import LearningCompounder
from .authority_boundary import EnterpriseAuthorityBoundary
from .state_store import EnterpriseOptimizationState
from .audit import EnterpriseOptimizationAudit

class CEOEnterpriseOptimizer:
    def __init__(self,root):
        self.state=EnterpriseOptimizationState(root)
        self.audit=EnterpriseOptimizationAudit(root)

    def run(self, ventures=None, capital=0, initiatives=None, departments=None, agents=None,
            work=None, lessons=None, actions=None):
        scorecard=EnterpriseScorecard().evaluate(ventures or [])
        allocations=EnterpriseCapitalAllocator().allocate(scorecard,capital)
        pruning=VenturePruner().decide(scorecard)
        strategy=StrategyAllocator().allocate(initiatives or [])
        capacity=DepartmentCapacityPlanner().plan(departments or [])
        talent=TalentAllocator().assign(agents or [],work or [])
        profitability=ProfitabilityEngine().evaluate(ventures or [])
        risk=PortfolioRiskEngine().evaluate(ventures or [])
        scenario=PortfolioScenarioEngine().model(ventures or [])
        learning=LearningCompounder().compound(lessons or [])
        next_actions=EnterpriseOptimizationLoop().next_actions(scorecard,pruning,capacity,risk)
        boundaries=[{**a,**EnterpriseAuthorityBoundary().evaluate(a)} for a in (actions or [])]

        result={
            "success":True,
            "status":"autonomous_enterprise_optimization_portfolio_cycle_complete",
            "scorecard":scorecard,
            "capital_allocations":allocations,
            "venture_decisions":pruning,
            "strategic_initiatives":strategy,
            "department_capacity":capacity,
            "talent_assignments":talent,
            "profitability":profitability,
            "portfolio_risk":risk,
            "scenario_model":scenario,
            "learning":learning,
            "next_actions":next_actions,
            "authority_boundaries":boundaries
        }
        self.state.save(result)
        self.audit.append("enterprise_optimization_cycle",result)
        return result
