from .priority_engine import PriorityEngine
from .goal_decomposer import GoalDecomposer
from .planning_horizons import PlanningHorizons
from .agent_registry import AgentRegistry
from .dynamic_staffing import DynamicStaffingManager
from .performance_manager import AgentPerformanceManager
from .task_market import DepartmentTaskMarket
from .budget_arbitrator import BudgetArbitrator
from .resource_conflict_resolver import ResourceConflictResolver
from .venture_coordinator import VentureCoordinator
from .strategy_scorecard import StrategyScorecard
from .failure_recovery import OrganizationalFailureRecovery
from .approval_router import ApprovalRouter
from .operating_cadence import OperatingCadence
from .executive_loop import ExecutiveDecisionLoop
from .decision_memory import DecisionMemory
from .organization_state import OrganizationState
from .org_audit import OrganizationAudit

class CEOOrganizationController:
    def __init__(self, root):
        self.root=root
        self.registry=AgentRegistry(root)
        self.memory=DecisionMemory(root)
        self.state=OrganizationState(root)
        self.audit=OrganizationAudit(root)

    def run(self, strategic_goal, tasks=None, departments=None, workload=None, agent_results=None,
            budget_requests=None, total_budget=0, resource_claims=None, ventures=None,
            outcomes=None, failures=None, actions=None):

        goals=GoalDecomposer().decompose(strategic_goal)
        horizons=PlanningHorizons().build(goals)
        ranked_tasks=PriorityEngine().rank(tasks or [])
        assignments=DepartmentTaskMarket().assign(ranked_tasks,departments or [])
        hires=DynamicStaffingManager().evaluate(workload or {},self.registry)
        performance=AgentPerformanceManager().evaluate(agent_results or [])
        budget=BudgetArbitrator().allocate(budget_requests or [],total_budget)
        conflicts=ResourceConflictResolver().resolve(resource_claims or [])
        venture_actions=VentureCoordinator().coordinate(ventures or [])
        scorecard=StrategyScorecard().evaluate(goals,outcomes or {})
        recovery=OrganizationalFailureRecovery().evaluate(failures or [])
        routed=ApprovalRouter().route(actions or [])
        cadence=OperatingCadence()
        loop=ExecutiveDecisionLoop().run(ranked_tasks,scorecard,recovery)

        result={
            "success":True,
            "status":"self_managing_ai_organization_cycle_complete",
            "strategic_goal":strategic_goal,
            "goal_decomposition":goals,
            "planning_horizons":horizons,
            "ranked_tasks":ranked_tasks,
            "assignments":assignments,
            "dynamic_hires":hires,
            "agent_performance":performance,
            "budget_arbitration":budget,
            "resource_conflicts":conflicts,
            "venture_coordination":venture_actions,
            "strategy_scorecard":scorecard,
            "failure_recovery":recovery,
            "authority_routing":routed,
            "operating_cadence":{
                "daily":cadence.daily(),
                "weekly":cadence.weekly(),
                "monthly":cadence.monthly(),
            },
            "executive_loop":loop,
        }

        self.state.save(result)
        self.memory.append("organization_cycle",result)
        self.audit.append(result)
        return result
