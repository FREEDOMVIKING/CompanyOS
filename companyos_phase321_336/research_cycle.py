from __future__ import annotations
from .source_scheduler import SourceScheduler
from .live_collector import LiveCollector
from .connector_health import ConnectorHealth
from companyos_phase301_320 import DiscoveryOrchestrator

class LiveResearchCycle:
    """334: configured live sources -> evidence -> CEO opportunity discovery."""

    def __init__(self, project_root):
        self.project_root = project_root
        self.scheduler = SourceScheduler()
        self.collector = LiveCollector()
        self.health = ConnectorHealth()
        self.discovery = DiscoveryOrchestrator(project_root)

    def run(self, sources):
        ordered = self.scheduler.order(sources)
        collection = self.collector.collect(ordered)
        result = {
            "success": bool(collection["records"]),
            "status": "live_research_collection_completed",
            "collection": collection,
            "connector_health": self.health.summarize(collection),
        }
        if collection["records"]:
            result["discovery"] = self.discovery.run(collection["records"])
        return result
