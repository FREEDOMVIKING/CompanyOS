from .runtime_profile import RuntimeProfile
from .startup_preflight import StartupPreflight
from .service_graph import ServiceGraph
from .supervisor import ProductionSupervisor
from .continuous_cycle import ContinuousCompanyCycle
from .scheduler import ProductionScheduler
from .mission_router import MissionRouter
from .approval_bridge import ProductionApprovalBridge
from .checkpoint_chain import CheckpointChain
from .recovery_manager import ProductionRecoveryManager
from .observability import ProductionObservability
from .readiness_gate import ProductionReadinessGate
from .runtime_state import ProductionRuntimeState
from .runtime_audit import ProductionRuntimeAudit

class CEOProductionRuntime:
    def __init__(self, root):
        self.root=root
        self.state=ProductionRuntimeState(root)
        self.audit=ProductionRuntimeAudit(root)
        self.checkpoints=CheckpointChain(root)

    def run_cycle(self, current_stage="discover", missions=None, services=None,
                  approval_queue=None, failures=None, preflight_checks=None):
        profile=RuntimeProfile().build()
        preflight=StartupPreflight().evaluate(preflight_checks or {})
        graph=ServiceGraph().build()
        supervised=ProductionSupervisor().evaluate(services or [])
        cycle=ContinuousCompanyCycle().plan(current_stage)
        scheduled=ProductionScheduler().schedule(missions or [])
        routed=[MissionRouter().route(m) for m in scheduled]
        approvals=ProductionApprovalBridge().summarize(approval_queue or [])
        previous=self.checkpoints.latest()
        recovery=ProductionRecoveryManager().plan(previous,failures or [])
        observability=ProductionObservability().snapshot(
            services or [],routed,approvals,recovery
        )
        readiness=ProductionReadinessGate().evaluate(
            preflight,observability,approvals
        )

        result={
            "success":True,
            "status":"autonomous_company_production_runtime_cycle_complete",
            "profile":profile,
            "preflight":preflight,
            "service_graph":graph,
            "service_supervision":supervised,
            "cycle":cycle,
            "scheduled_missions":routed,
            "approval_summary":approvals,
            "recovery":recovery,
            "observability":observability,
            "production_readiness":readiness
        }

        checkpoint=self.checkpoints.save(result)
        result["checkpoint"]=checkpoint
        self.state.save(result)
        self.audit.append("production_cycle",result)
        return result
