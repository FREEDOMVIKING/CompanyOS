from .fallback_chain import FallbackChain
from .evidence_collector import EvidenceCollector
from .evidence_merger import EvidenceMerger
from .provider_error_normalizer import ProviderErrorNormalizer
from .failover_sequencer import FailoverSequencer
from .source_quota import SourceQuota
from .diversity_gate import DiversityGate
from .completion_policy import CompletionPolicy
from .partial_result_store import PartialResultStore
from .provider_execution_audit import ProviderExecutionAudit
from .research_packet_assembler import ResearchPacketAssembler
from .lifecycle_evidence_output import LifecycleEvidenceOutput

class CEOMultiProviderBridge:
    """792: execute autonomous multi-provider research collection."""
    def __init__(self,root):
        self.root=root
        self.partial=PartialResultStore(root)
        self.audit=ProviderExecutionAudit(root)

    def execute(self, mission, query, query_type, preferred_provider, providers, context=None):
        chain=FallbackChain().build(preferred_provider,query_type,[])
        batches=[]
        execution=[]
        mission_id=mission.get("mission_id","unknown")

        for idx,provider in enumerate(chain):
            batch=EvidenceCollector().collect(provider,query,context or {})
            batches.append(batch)
            merged=EvidenceMerger().merge(batches)
            err=ProviderErrorNormalizer().normalize(batch)
            step=FailoverSequencer().next(idx,chain,err,len(merged),target_min=3)
            execution.append({
                "provider":provider,
                "success":batch.get("success"),
                "error":batch.get("error"),
                "error_kind":err.get("kind"),
                "evidence_count":len(batch.get("items",[])),
                "continue":step.get("continue"),
                "reason":step.get("reason"),
            })
            self.partial.save(mission_id,merged)
            self.audit.append({"mission_id":mission_id,"provider":provider,"result":execution[-1]})
            if not step.get("continue"):
                break

        merged=EvidenceMerger().merge(batches)
        quota=SourceQuota().apply(merged,max_per_provider=5)
        evidence=quota["kept"]
        packet=ResearchPacketAssembler().assemble(providers,evidence,[])
        diversity=DiversityGate().evaluate(evidence)
        completion=CompletionPolicy().decide(
            packet.get("confidence",0),
            diversity.get("passed",False),
            (packet.get("completeness") or {}).get("complete",False),
            provider_chain_exhausted=(len(execution)>=len(chain)),
        )
        return {
            "success":True,
            "status":"multi_provider_research_execution_complete",
            "provider_chain":chain,
            "execution":execution,
            "evidence":evidence,
            "dropped_by_quota":quota["dropped"],
            "packet":packet,
            "diversity_gate":diversity,
            "completion":completion,
            "lifecycle_evidence":LifecycleEvidenceOutput().build(packet),
        }
