from __future__ import annotations
from .fetch_budget import FetchBudget

class LiveResearchRuntime:
    """336: runtime status for live source connectors."""

    def status(self):
        return {
            "success": True,
            "status": "phase336_live_research_connectors_ready",
            "supported_source_types": ["rss","atom","json","text"],
            "bounded_fetching": True,
            "source_priority": True,
            "provenance_tracking": True,
            "connector_health": True,
            "ceo_discovery_bridge": True,
            "fetch_limits": FetchBudget().limits(),
            "autonomy_mode": "high",
        }
