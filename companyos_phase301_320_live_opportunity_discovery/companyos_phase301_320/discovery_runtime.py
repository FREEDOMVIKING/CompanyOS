from __future__ import annotations
from .research_config import ResearchConfig

class DiscoveryRuntime:
    """320: runtime status for live opportunity-discovery foundation."""

    def __init__(self, project_root=None):
        self.config = ResearchConfig(project_root)

    def status(self):
        return {
            "success": True,
            "status": "phase320_live_opportunity_discovery_ready",
            "research_config": self.config.load(),
            "pluggable_live_sources": True,
            "persistent_evidence_store": True,
            "deduplication": True,
            "problem_mining": True,
            "market_mapping": True,
            "competitor_signals": True,
            "trend_detection": True,
            "economic_ranking": True,
            "validation_queue": True,
            "provider_assisted_synthesis": True,
            "autonomy_mode": "high",
        }
