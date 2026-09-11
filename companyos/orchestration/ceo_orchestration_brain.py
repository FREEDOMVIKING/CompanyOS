from .goal_graph import PersistentGoalGraph
from .capability_registry import CapabilityRegistry
from .agent_factory import DynamicAgentFactory
from .cross_system_scheduler import CrossSystemScheduler
from .memory_consolidation import MemoryConsolidationEngine
from .decision_synthesizer import DecisionSynthesizer
from .priority_arbitrator import PriorityArbitrator
from .dependency_resolver import DependencyResolver
from .system_health import UnifiedSystemHealth
from .restart_safe_runtime import RestartSafeRuntime
from .continuous_loop import ContinuousAutonomyLoop
from .authority_router import AuthorityRouter
from .orchestration_state import OrchestrationState
from .orchestration_audit import OrchestrationAudit

class CEOOrchestrationBrain:
    def __init__(self, root):
        self.root=root
        self.goals=PersistentGoalGraph(root)
        self.state=OrchestrationState(root)
        self.audit=OrchestrationAudit(root)

    def run(self, strategic_goals=None, systems=None, work_items=None, memories=None,
            signals=None, checkpoint=None, inflight=None, actions=None):
        for g in strategic_goals or []:
            self.goals.upsert_goal(g["goal_id"],g["objective"],g.get("priority",.5),g.get("status","active"))

        registry=CapabilityRegistry().build(systems or [])
        required=sorted(set(w.get("capability") for w in (work_items or []) if w.get("capability")))
        spawned=DynamicAgentFactory().fill_gaps(required,registry)

        ranked=PriorityArbitrator().rank(work_items or [])
        ordered=DependencyResolver().order(ranked)
        scheduled=CrossSystemScheduler().schedule(ordered,registry)
        memory=MemoryConsolidationEngine().consolidate(memories or [])
        decision=DecisionSynthesizer().synthesize(signals or [])
        health=UnifiedSystemHealth().evaluate(systems or [])
        recovery=RestartSafeRuntime().recover(checkpoint,inflight or [])
        authority=AuthorityRouter().route(actions or [])
        next_cycle=ContinuousAutonomyLoop().next_cycle(health,decision,ranked)

        result={
            "success":True,
            "status":"unified_autonomous_orchestration_cycle_complete",
            "goal_graph":self.goals.load(),
            "capability_registry":registry,
            "dynamic_agents_spawned":spawned,
            "ranked_work":ranked,
            "dependency_order":ordered,
            "scheduled_work":scheduled,
            "memory_consolidation":memory,
            "decision_synthesis":decision,
            "system_health":health,
            "restart_recovery":recovery,
            **authority,
            "next_cycle":next_cycle
        }
        self.state.save(result)
        self.audit.append("orchestration_cycle",result)
        return result
