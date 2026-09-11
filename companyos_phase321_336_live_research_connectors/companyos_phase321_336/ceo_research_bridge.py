from __future__ import annotations
from .source_registry import SourceRegistry
from .research_cycle import LiveResearchCycle

class CEOResearchBridge:
    """335: one-call CEO bridge from configured sources to validation queue."""

    def __init__(self, project_root):
        self.registry = SourceRegistry(project_root)
        self.cycle = LiveResearchCycle(project_root)

    def run(self):
        cfg = self.registry.load()
        sources = cfg.get("sources", [])
        if not sources:
            return {
                "success": False,
                "status": "no_live_research_sources_configured",
                "reason": "configure_research_sources_first",
            }
        return self.cycle.run(sources)
