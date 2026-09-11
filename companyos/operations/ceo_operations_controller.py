from .goal_tracker import PersistentGoalTracker
from .memory_consolidator import MemoryConsolidator
from .background_scheduler import BackgroundJobScheduler
from .department_coordinator import CrossDepartmentCoordinator
from .continuous_optimizer import ContinuousBusinessOptimizer
from .failure_recovery import PersistentFailureRecovery
from .learning_loop import OrganizationalLearningLoop
from .operating_metrics import OperatingMetrics
from .initiative_manager import InitiativeManager
from .policy_engine import OperatingPolicyEngine
from .cycle_state import ContinuousCycleState
from .ops_audit import OperationsAudit

class CEOOperationsController:
    def __init__(self, root):
        self.root=root
        self.goals=PersistentGoalTracker(root)
        self.state=ContinuousCycleState(root)
        self.audit=OperationsAudit(root)

    def run(self, goals=None, events=None, cadence=None, department_updates=None,
            metrics=None, failures=None, experiments=None, decisions=None,
            initiatives=None, actions=None):

        tracked=[]
        for g in goals or []:
            tracked.append(self.goals.upsert(
                g["goal_id"],g["objective"],g.get("target",1),g.get("progress",0),g.get("horizon","weekly")
            ))

        schedule=BackgroundJobScheduler().build(
            (cadence or {}).get("daily",[]),
            (cadence or {}).get("weekly",[]),
            (cadence or {}).get("monthly",[])
        )

        memory=MemoryConsolidator().consolidate(events or [])
        coordination=CrossDepartmentCoordinator().coordinate(department_updates or [])
        operating=OperatingMetrics().score(metrics or {})
        optimizations=ContinuousBusinessOptimizer().recommend(metrics or {})
        recovery=PersistentFailureRecovery().plan(failures or [])
        learning=OrganizationalLearningLoop().learn(experiments or [],decisions or [])
        ranked=InitiativeManager().prioritize(initiatives or [])
        policies=OperatingPolicyEngine().evaluate(actions or [])

        result={
            "success":True,
            "status":"persistent_autonomous_operations_cycle_complete",
            "goals":tracked,
            "background_schedule":schedule,
            "memory_consolidation":memory,
            "cross_department_coordination":coordination,
            "operating_metrics":operating,
            "optimization_actions":optimizations,
            "failure_recovery":recovery,
            "organizational_learning":learning,
            "ranked_initiatives":ranked,
            "authority_routing":policies,
            "next_cycle":{
                "continue":True,
                "focus":ranked[:3],
                "optimize":optimizations[:3],
                "recover":recovery[:3]
            }
        }

        self.state.save(result)
        self.audit.append("operations_cycle",result)
        return result
