from .relevance_filter import RelevanceFilter
from .semantic_deduper import SemanticDeduper
from .evidence_scorer import EvidenceScorer
from .commercial_intent import CommercialIntent
from .pain_signal import PainSignal
from .market_plausibility import MarketPlausibility
from .competitor_signal import CompetitorSignal
from .cross_signal_synthesizer import CrossSignalSynthesizer
from .opportunity_quality import OpportunityQuality
from .decision_brain import OpportunityDecisionBrain

class OpportunityQualityPipeline:
    """526: records -> filtered evidence -> synthesized candidates -> decisions."""

    def __init__(self):
        self.relevance = RelevanceFilter()
        self.deduper = SemanticDeduper()
        self.evidence = EvidenceScorer()
        self.intent = CommercialIntent()
        self.pain = PainSignal()
        self.market = MarketPlausibility()
        self.competitor = CompetitorSignal()
        self.synth = CrossSignalSynthesizer()
        self.quality = OpportunityQuality()
        self.brain = OpportunityDecisionBrain()

    def run(self, records):
        filtered = self.relevance.apply(records)
        unique = self.deduper.unique(filtered["accepted"])
        clusters = self.synth.synthesize(unique)
        candidates = []

        for cluster in clusters:
            rs = cluster["records"]
            if not rs:
                continue
            dims = {
                "relevance": round(sum(float(r.get("relevance_score",0)) for r in rs)/len(rs),2),
                "evidence": round(sum(self.evidence.score(r) for r in rs)/len(rs),2),
                "pain": round(sum(self.pain.score(r) for r in rs)/len(rs),2),
                "commercial_intent": round(sum(self.intent.score(r) for r in rs)/len(rs),2),
                "market_plausibility": round(sum(self.market.score(r) for r in rs)/len(rs),2),
                "cross_source": min(10, len(cluster["sources"]) * 3.5),
            }

            competitor = [self.competitor.analyze(r) for r in rs]
            candidate = {
                "name": cluster["theme"].replace("_"," ").title(),
                "theme": cluster["theme"],
                "evidence_count": len(rs),
                "source_count": len(cluster["sources"]),
                "sources": cluster["sources"],
                "evidence_links": list(dict.fromkeys(r.get("url") for r in rs if r.get("url"))),
                "dimensions": dims,
                "competitor_signals": competitor,
            }
            candidate["quality_score"] = self.quality.score(candidate)
            candidate["decision"] = self.brain.evaluate(candidate)
            candidates.append(candidate)

        candidates.sort(key=lambda x:x["quality_score"], reverse=True)
        return {
            "success": True,
            "status": "opportunity_quality_pipeline_completed",
            "records_received": len(records),
            "records_relevant": len(filtered["accepted"]),
            "records_rejected": len(filtered["rejected"]),
            "records_after_dedupe": len(unique),
            "candidates": candidates,
            "top_candidate": candidates[0] if candidates else None,
        }
