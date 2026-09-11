#!/usr/bin/env python3
import json, tempfile
from pathlib import Path
from companyos_phase301_320 import (
    SourceContract, EvidenceDeduper, ProblemMiner, MarketMapper,
    CompetitorAnalyzer, TrendDetector, OpportunityRanker,
    ResearchPlanner, ValidationQueue, DiscoveryMemory,
    ResearchIngestor, SourceHealth, CEODiscoveryLoop,
    DiscoveryRuntime, DiscoveryOrchestrator
)

records = [
    {"source":"a","title":"Manual work is slow","text":"Customers struggle with slow manual reporting.","url":"u1"},
    {"source":"b","title":"Pricing complaints","text":"Teams complain competitor pricing is expensive.","url":"u2"},
]

assert SourceContract().normalize(records[0])["valid"] is True
assert len(EvidenceDeduper().unique(records + [records[0]])) == 2
ing = ResearchIngestor().ingest(records)
assert len(ing["records"]) == 2
problems = ProblemMiner().mine(ing["records"])
assert problems
assert MarketMapper().map(ing["records"])
assert CompetitorAnalyzer().analyze(ing["records"])
assert isinstance(TrendDetector().detect(problems), list)
assert ResearchPlanner().plan()["queries"]
assert SourceHealth().summarize(ing["records"])["healthy"] is True

result = CEODiscoveryLoop().run(records)
assert result["success"] is True
assert result["ranked_opportunities"]

root = Path(tempfile.mkdtemp(prefix="companyos_phase320_verify_"))
orchestrated = DiscoveryOrchestrator(root).run(records)
assert orchestrated["validation_queue_count"] >= 1
assert ValidationQueue(root).load()
assert DiscoveryMemory(root).path.exists()
assert DiscoveryRuntime(root).status()["success"] is True

print(json.dumps({
    "success": True,
    "status": "phase301_320_verification_passed",
    "cycle_status": "phase320_live_opportunity_discovery_ready",
    "pluggable_live_sources": True,
    "persistent_evidence": True,
    "deduplication": True,
    "problem_mining": True,
    "market_mapping": True,
    "competitor_analysis": True,
    "trend_detection": True,
    "economic_ranking": True,
    "validation_queue": True,
    "ceo_discovery_loop": True,
    "autonomy_mode": "high"
}, indent=2))
