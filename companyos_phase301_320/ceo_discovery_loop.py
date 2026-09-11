from __future__ import annotations
from .research_ingestor import ResearchIngestor
from .problem_miner import ProblemMiner
from .market_mapper import MarketMapper
from .competitor_analyzer import CompetitorAnalyzer
from .trend_detector import TrendDetector
from .opportunity_synthesizer import OpportunitySynthesizer
from .opportunity_ranker import OpportunityRanker
from .source_health import SourceHealth
from .research_planner import ResearchPlanner

class CEODiscoveryLoop:
    """318: evidence -> problems -> opportunities -> ranked validation candidates."""

    def __init__(self):
        self.ingestor = ResearchIngestor()
        self.problem_miner = ProblemMiner()
        self.market_mapper = MarketMapper()
        self.competitors = CompetitorAnalyzer()
        self.trends = TrendDetector()
        self.synthesizer = OpportunitySynthesizer()
        self.ranker = OpportunityRanker()
        self.source_health = SourceHealth()
        self.planner = ResearchPlanner()

    def run(self, records):
        ingested = self.ingestor.ingest(records)
        evidence = ingested["records"]
        problems = self.problem_miner.mine(evidence)
        markets = self.market_mapper.map(evidence)
        competitors = self.competitors.analyze(evidence)
        trends = self.trends.detect(problems)
        opportunities = self.synthesizer.synthesize(
            problems, markets, competitors, limit=10
        )
        ranked = self.ranker.rank(opportunities)
        return {
            "success": True,
            "status": "opportunity_discovery_completed",
            "evidence_count": len(evidence),
            "rejected_count": len(ingested["rejected"]),
            "problem_count": len(problems),
            "market_themes": markets,
            "competitor_signals": competitors,
            "trends": trends,
            "ranked_opportunities": ranked,
            "source_health": self.source_health.summarize(evidence),
            "next_research_plan": self.planner.plan([x["theme"] for x in markets[:5]]),
        }
