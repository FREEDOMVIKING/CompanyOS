from .artifact_verifier import ArtifactVerifier
from .deployment_orchestrator import DeploymentOrchestrator
from .irreversible_action_gate import IrreversibleActionGate
from .launch_monitor import LaunchMonitor
from .customer_feedback_loop import CustomerFeedbackLoop
from .revenue_telemetry import RevenueTelemetry
from .growth_metric_engine import GrowthMetricEngine
from .incident_detector import IncidentDetector
from .incident_recovery import IncidentRecovery
from .post_launch_optimizer import PostLaunchOptimizer
from .portfolio_feedback import PortfolioFeedback
from .launch_state_store import LaunchStateStore
from .launch_audit import LaunchAudit

class CEOLaunchOperateController:
    """1093-1098: unified release-candidate -> launch -> operate controller."""
    def __init__(self, root):
        self.root=root
        self.state=LaunchStateStore(root)
        self.audit=LaunchAudit(root)

    def run(self, venture_id, release_candidate, artifact_path=None, expected_sha256=None,
            environment="staging", deployment_approvals=None, launch_metrics=None,
            customer_feedback=None, revenue_inputs=None, growth_metrics=None,
            business_risk_metrics=None):

        artifact=ArtifactVerifier().verify(
            artifact_path=artifact_path,
            expected_sha256=expected_sha256,
        ) if artifact_path else {"passed":True,"exists":True,"sha256":None}

        if not release_candidate.get("passed"):
            return {
                "success":False,
                "status":"launch_blocked_release_candidate_not_ready",
                "artifact":artifact,
            }

        if not artifact.get("passed"):
            return {
                "success":False,
                "status":"launch_blocked_artifact_verification_failed",
                "artifact":artifact,
            }

        deployment_plan=DeploymentOrchestrator().plan(release_candidate,environment)

        # Explicitly gate any irreversible production action.
        if environment=="production":
            gate=IrreversibleActionGate().evaluate("production_traffic_cutover")
            if gate["requires_approval"] and not (deployment_approvals or {}).get("production_traffic_cutover",False):
                return {
                    "success":False,
                    "status":"launch_waiting_for_explicit_approval",
                    "approval_gate":gate,
                    "deployment_plan":deployment_plan,
                }

        deployment=DeploymentOrchestrator().execute(deployment_plan,deployment_approvals or {})
        health=LaunchMonitor().evaluate(launch_metrics or {})
        feedback=CustomerFeedbackLoop().summarize(customer_feedback or [])

        revenue_inputs=revenue_inputs or {}
        revenue=RevenueTelemetry().compute(
            revenue=revenue_inputs.get("revenue",0),
            customers=revenue_inputs.get("customers",0),
            spend=revenue_inputs.get("spend",0),
            refunds=revenue_inputs.get("refunds",0),
        )

        growth=GrowthMetricEngine().compute(growth_metrics or {})
        incidents=IncidentDetector().detect(health,business_risk_metrics or {})
        recovery=IncidentRecovery().plan(incidents,rollback_ready=True)
        optimizations=PostLaunchOptimizer().plan(health,growth,feedback)
        portfolio=PortfolioFeedback().summarize(
            venture_id,health,revenue,growth,incidents
        )

        result={
            "success":True,
            "status":"launch_operate_cycle_complete",
            "venture_id":venture_id,
            "artifact":artifact,
            "deployment_plan":deployment_plan,
            "deployment":deployment,
            "launch_health":health,
            "customer_feedback":feedback,
            "revenue":revenue,
            "growth":growth,
            "incidents":incidents,
            "recovery":recovery,
            "optimizations":optimizations,
            "portfolio_feedback":portfolio,
        }

        self.state.save(venture_id,result)
        self.audit.append(result)
        return result
