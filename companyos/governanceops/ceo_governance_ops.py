from .policy_registry import PolicyRegistry
from .compliance_matrix import ComplianceMatrix
from .control_evidence import ControlEvidenceCollector
from .decision_ledger import DecisionLedger
from .data_governance import DataGovernanceEngine
from .retention_policy import RetentionPolicyEngine
from .access_review import AccessReviewEngine
from .vendor_governance import VendorGovernanceEngine
from .compliance_monitor import ContinuousComplianceMonitor
from .audit_readiness import AuditReadinessEngine
from .exception_manager import PolicyExceptionManager
from .authority_boundary import GovernanceAuthorityBoundary
from .state_store import GovernanceState
from .audit import GovernanceAudit

class CEOGovernanceOpsController:
    def __init__(self,root):
        self.state=GovernanceState(root)
        self.audit=GovernanceAudit(root)
        self.ledger=DecisionLedger(root)

    def run(self, policies=None, requirements=None, controls=None, evidence=None,
            assets=None, records=None, identities=None, vendors=None, decisions=None,
            exceptions=None, actions=None):
        registry=PolicyRegistry().compile(policies or [])
        matrix=ComplianceMatrix().map(requirements or [],controls or [])
        evidence_rows=ControlEvidenceCollector().collect(controls or [],evidence or {})
        data=DataGovernanceEngine().classify(assets or [])
        retention=RetentionPolicyEngine().evaluate(records or [])
        access=AccessReviewEngine().review(identities or [])
        vendor=VendorGovernanceEngine().evaluate(vendors or [])
        monitor=ContinuousComplianceMonitor().evaluate(matrix,evidence_rows)
        ledger=[self.ledger.append(d) for d in (decisions or [])]
        exception_rows=[PolicyExceptionManager().evaluate(e) for e in (exceptions or [])]
        audit_ready=AuditReadinessEngine().score({
            "policy_registry":bool(registry),
            "control_mapping":bool(matrix),
            "evidence":all(x["evidence_present"] for x in evidence_rows) if evidence_rows else False,
            "decision_ledger":bool(ledger),
            "access_review":access["passed"]
        })
        boundaries=[{**a,**GovernanceAuthorityBoundary().evaluate(a)} for a in (actions or [])]

        result={
            "success":True,
            "status":"autonomous_governance_compliance_cycle_complete",
            "policy_registry":registry,
            "compliance_matrix":matrix,
            "control_evidence":evidence_rows,
            "data_governance":data,
            "retention_policy":retention,
            "access_review":access,
            "vendor_governance":vendor,
            "continuous_compliance":monitor,
            "decision_ledger_entries":ledger,
            "policy_exceptions":exception_rows,
            "audit_readiness":audit_ready,
            "authority_boundaries":boundaries
        }
        self.state.save(result)
        self.audit.append("governance_cycle",result)
        return result
