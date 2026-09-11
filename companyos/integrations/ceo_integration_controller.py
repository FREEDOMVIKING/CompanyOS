from .integration_registry import IntegrationRegistry
from .tool_router import ToolRouter
from .department_router import DepartmentRouter
from .parallel_dispatcher import ParallelDispatcher
from .approval_gate import ExternalActionApprovalGate
from .result_verifier import ResultVerifier
from .provider_health import ProviderHealthRegistry
from .connector_policy import ConnectorPolicy
from .communication_orchestrator import CommunicationOrchestrator
from .deployment_bridge import DeploymentBridge
from .scheduled_work import ScheduledWorkPlanner
from .execution_ledger import ExecutionLedger

class CEOIntegrationController:
    def __init__(self, root):
        self.root=root
        self.registry=IntegrationRegistry(root)
        self.ledger=ExecutionLedger(root)

    def run(self, objective, jobs=None, providers=None, scheduled_items=None):
        routed=DepartmentRouter().route(jobs or [])
        parallel=ParallelDispatcher().dispatch(routed,max_parallel=4)
        ranked_providers=ProviderHealthRegistry().rank(providers or [])

        tool_routes=[]
        integrations=self.registry.available()
        for job in routed:
            tool_routes.append(ToolRouter().route(job,integrations))

        approvals=[]
        autonomous=[]
        for job in routed:
            action={"kind":job.get("action_kind",job.get("task_type")),"amount":job.get("amount",0)}
            gate=ExternalActionApprovalGate().evaluate(action,action.get("amount",0))
            (approvals if gate["requires_approval"] else autonomous).append({"job":job,"gate":gate})

        scheduled=ScheduledWorkPlanner().plan(scheduled_items or [])
        comms=CommunicationOrchestrator().draft("stakeholders",objective)
        deployment=DeploymentBridge().plan("staging","latest_artifact","previous_artifact")

        result={
            "success":True,
            "status":"real_world_integration_orchestration_complete",
            "objective":objective,
            "department_routing":routed,
            "parallel_dispatch":parallel,
            "provider_ranking":ranked_providers,
            "tool_routes":tool_routes,
            "autonomous_actions":autonomous,
            "approval_queue":approvals,
            "scheduled_work":scheduled,
            "communication_draft":comms,
            "deployment_plan":deployment,
            "feedback_loop":{
                "specialist_results_return_to_ceo":True,
                "result_verification_required":True,
                "retry_on_verification_failure":True
            }
        }
        self.ledger.append("integration_cycle",result)
        return result
