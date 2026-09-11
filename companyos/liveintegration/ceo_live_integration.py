from .connector_certification import ConnectorCertification
from .preflight import LivePreflight
from .credential_readiness import CredentialReadiness
from .live_mode_gate import LiveModeGate
from .provider_failover import ProviderFailover
from .transaction_boundary import TransactionBoundary
from .request_sanitizer import RequestSanitizer
from .live_observability import LiveIntegrationObservability
from .integration_state import LiveIntegrationState
from .integration_audit import LiveIntegrationAudit

class CEOLiveIntegrationController:
    def __init__(self,root):
        self.state=LiveIntegrationState(root)
        self.audit=LiveIntegrationAudit(root)

    def run(self, connectors=None, actions=None, attempts=None, env_requirements=None, approvals=None):
        certifications=[ConnectorCertification().certify(x) for x in (connectors or [])]
        credential_status=CredentialReadiness().check(env_requirements or [])
        preflight=LivePreflight().evaluate({
            "connector_certified":all(x["certified"] for x in certifications) if certifications else False,
            "credentials_ready":credential_status["ready"],
            "health_ok":all(float(x.get("health_score",0))>=.7 for x in (connectors or [])) if connectors else False,
            "rollback_ready":True,
            "audit_ready":True
        })
        provider_choice=ProviderFailover().choose(connectors or [])
        approval_set=set(approvals or [])
        routed=[]
        for a in actions or []:
            gate=LiveModeGate().evaluate(a,preflight,approval=a.get("kind") in approval_set)
            routed.append({
                "action":RequestSanitizer().sanitize(a),
                "boundary":TransactionBoundary().classify(a),
                "gate":gate
            })
        observability=LiveIntegrationObservability().summarize(attempts or [])
        result={
            "success":True,
            "status":"secure_live_integration_runtime_cycle_complete",
            "connector_certifications":certifications,
            "credential_readiness":credential_status,
            "live_preflight":preflight,
            "provider_choice":provider_choice,
            "routed_actions":routed,
            "observability":observability
        }
        self.state.save(result)
        self.audit.append("live_integration_cycle",result)
        return result
