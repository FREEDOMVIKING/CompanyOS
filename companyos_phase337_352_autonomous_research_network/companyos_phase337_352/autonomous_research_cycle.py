from __future__ import annotations
from pathlib import Path
from companyos_phase321_336 import SourceRegistry, LiveCollector
from companyos_phase301_320 import (
    ResearchIngestor, ProblemMiner, CompetitorAnalyzer, OpportunityRanker,
    ValidationQueue, DiscoveryMemory
)
from .freshness_filter import FreshnessFilter
from .quality_gate import ResearchQualityGate
from .problem_clusterer import ProblemClusterer
from .gap_detector import MarketGapDetector
from .competitor_pressure import CompetitorPressure
from .opportunity_builder import EvidenceOpportunityBuilder
from .confidence_engine import OpportunityConfidence
from .validation_router import ValidationRouter
from .ceo_decision_input import CEODecisionInput
from .network_health import ResearchNetworkHealth

class AutonomousResearchCycle:
    """351: live sources -> quality evidence -> gaps -> ranked CEO decision input."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.registry = SourceRegistry(self.root)
        self.collector = LiveCollector()
        self.ingestor = ResearchIngestor()
        self.freshness = FreshnessFilter()
        self.quality = ResearchQualityGate()
        self.problem_miner = ProblemMiner()
        self.competitors = CompetitorAnalyzer()
        self.clusterer = ProblemClusterer()
        self.gaps = MarketGapDetector()
        self.pressure = CompetitorPressure()
        self.builder = EvidenceOpportunityBuilder()
        self.rank = OpportunityRanker()
        self.confidence = OpportunityConfidence()
        self.router = ValidationRouter()
        self.queue = ValidationQueue(self.root)
        self.memory = DiscoveryMemory(self.root)
        self.network = ResearchNetworkHealth()
        self.ceo = CEODecisionInput()

    def run(self):
        sources = self.registry.load().get("sources", [])
        enabled = [s for s in sources if s.get("enabled", True)]
        if not enabled:
            return {
                "success": False,
                "status": "no_enabled_research_sources",
                "reason": "configure_and_enable_sources",
            }

        collection = self.collector.collect(enabled)
        health = self.network.summarize(enabled, collection)
        ingested = self.ingestor.ingest(collection.get("records", []))
        fresh = self.freshness.filter(ingested["records"])
        quality = self.quality.apply(fresh)
        problems = self.problem_miner.mine(quality["accepted"])
        competitors = self.competitors.analyze(quality["accepted"])
        clusters = self.clusterer.cluster(problems)
        gaps = self.gaps.detect(clusters, competitors)
        opportunities = self.builder.build(gaps, clusters)
        ranked = self.rank.rank(opportunities)

        for item in ranked:
            if item.get("valid"):
                item["confidence"] = self.confidence.score(
                    item["opportunity"],
                    source_count=health["diversity_score"]
                )

        routed = self.router.route(ranked)
        queued = self.queue.save(routed)
        decision = self.ceo.build(routed, health)

        result = {
            "success": bool(routed),
            "status": "autonomous_live_research_cycle_completed",
            "network_health": health,
            "quality": {
                "accepted": len(quality["accepted"]),
                "rejected": len(quality["rejected"]),
            },
            "problem_count": len(problems),
            "clusters": clusters,
            "competitor_pressure": self.pressure.score(competitors),
            "market_gaps": gaps,
            "ranked_opportunities": routed,
            "validation_queue_count": len(queued),
            "ceo_decision_input": decision,
        }
        result["memory"] = self.memory.record(result)
        return result
