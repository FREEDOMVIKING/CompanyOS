from .health_engine import CustomerHealthEngine
from .support_triage import SupportTriageEngine
from .success_planner import CustomerSuccessPlanner
from .churn_predictor import ChurnRiskEngine
from .renewal_engine import RenewalReadinessEngine
from .feedback_engine import FeedbackIntelligenceEngine
from .sla_engine import SLAEngine
from .knowledge_engine import CustomerKnowledgeEngine
from .escalation_engine import EscalationEngine
from .service_quality import ServiceQualityEngine
from .authority_boundary import CustomerAuthorityBoundary
from .state_store import CustomerOpsState
from .audit import CustomerOpsAudit

class CEOCustomerOpsController:
    def __init__(self,root):
        self.state=CustomerOpsState(root); self.audit=CustomerOpsAudit(root)
    def run(self,customers=None,tickets=None,feedback=None,resolved_tickets=None,service_signals=None,actions=None):
        health=CustomerHealthEngine().score(customers or [])
        triage=SupportTriageEngine().triage(tickets or [])
        plans=[CustomerSuccessPlanner().plan(c) for c in health]
        churn=ChurnRiskEngine().evaluate(customers or [])
        renewals=RenewalReadinessEngine().evaluate(health)
        feedback_summary=FeedbackIntelligenceEngine().summarize(feedback or [])
        sla=SLAEngine().evaluate(tickets or [])
        knowledge=CustomerKnowledgeEngine().learn(resolved_tickets or [])
        escalations=[EscalationEngine().decide(t) for t in triage]
        quality=ServiceQualityEngine().score(service_signals or {})
        boundaries=[{**a,**CustomerAuthorityBoundary().evaluate(a)} for a in (actions or [])]
        result={"success":True,"status":"autonomous_customer_success_service_cycle_complete",
                "customer_health":health,"support_triage":triage,"success_plans":plans,"churn_risk":churn,
                "renewal_readiness":renewals,"feedback_intelligence":feedback_summary,"sla":sla,
                "knowledge_drafts":knowledge,"escalations":escalations,"service_quality":quality,
                "authority_boundaries":boundaries}
        self.state.save(result); self.audit.append("customer_success_service_cycle",result); return result
