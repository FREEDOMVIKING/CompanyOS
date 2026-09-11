from companyos_phase745_760 import RetryBudget
from .provider_context import ProviderContext
from .provider_health_bridge import ProviderHealthBridge
from .evidence_quality_gate import EvidenceQualityGate
from .research_execution_policy import ResearchExecutionPolicy
from .fallback_cycle import FallbackCycle
from .research_result_adapter import ResearchResultAdapter
from .lifecycle_evidence_bridge import LifecycleEvidenceBridge
from .learning_evidence_bridge import LearningEvidenceBridge
from .research_retry_state import ResearchRetryState

class IntegratedResearchExecutor:
    """772: live provider-aware research quality orchestration."""
    def __init__(self,root):
        self.root=root
        self.retry=ResearchRetryState(root)

    def evaluate_result(self, mission, raw_result, providers):
        ctx=ProviderContext().build(mission)
        provider=ctx["current_provider"]
        evidence=ResearchResultAdapter().adapt(raw_result,provider)
        selected=ProviderHealthBridge(self.root).select(providers)
        quality=EvidenceQualityGate().evaluate(providers,evidence,[])
        used=self.retry.increment(mission.get("mission_id"),provider) if not quality["passed"] else ctx["attempts"]
        remaining=RetryBudget().remaining(provider,used)
        selected_name=(selected.get("selected") or {}).get("name")
        available=bool(selected_name)
        decision=ResearchExecutionPolicy().decide(quality,available,remaining)
        fallback=None
        if decision in ("fallback","retry") and not quality["passed"]:
            fallback=FallbackCycle().choose(provider,ctx["query_type"],[])
        return {
            "success":True,
            "status":"integrated_research_evaluated",
            "decision":decision,
            "selected_provider":selected_name,
            "fallback_provider":fallback,
            "quality":quality,
            "lifecycle_evidence":LifecycleEvidenceBridge().build(quality),
            "learning_evidence":LearningEvidenceBridge().build(quality),
            "retry_remaining":remaining,
        }
