from .provider_selector import ProviderSelector
from .research_normalizer import ResearchNormalizer
from .dedupe_evidence import DedupeEvidence
from .source_diversifier import SourceDiversifier
from .evidence_completeness import EvidenceCompleteness
from .contradiction_detector import ContradictionDetector
from .weak_signal_filter import WeakSignalFilter
from .evidence_confidence import EvidenceConfidence
class ResearchQualityRuntime:
    """760: unified research quality pipeline."""
    def run(self, providers, evidence, claims=None):
        provider=ProviderSelector().choose(providers)
        normalized=ResearchNormalizer().normalize(evidence)
        deduped=DedupeEvidence().dedupe(normalized)
        filtered=WeakSignalFilter().filter(deduped)
        kept=filtered["kept"]
        packet={
            "provider":provider.get("selected"),
            "evidence":kept,
            "dropped_evidence":filtered["dropped"],
            "diversity":SourceDiversifier().evaluate(kept),
            "completeness":EvidenceCompleteness().evaluate(kept),
            "contradictions":ContradictionDetector().detect(claims or []),
            "confidence":EvidenceConfidence().score(kept),
        }
        packet["success"]=True
        packet["status"]="phase760_provider_aware_research_quality_ready"
        return packet
