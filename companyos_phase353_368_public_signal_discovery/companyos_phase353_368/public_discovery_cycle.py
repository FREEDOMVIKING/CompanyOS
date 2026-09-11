from __future__ import annotations
from pathlib import Path
from companyos_phase301_320 import DiscoveryOrchestrator
from .public_signal_collector import PublicSignalCollector
from .discovery_input_builder import DiscoveryInputBuilder
from .opportunity_evidence_linker import OpportunityEvidenceLinker

class PublicDiscoveryCycle:
    """366: real public signals -> evidence -> opportunity discovery."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.collector = PublicSignalCollector()
        self.input_builder = DiscoveryInputBuilder()
        self.discovery = DiscoveryOrchestrator(self.root)
        self.linker = OpportunityEvidenceLinker()

    def run(self):
        collection = self.collector.collect()
        evidence = self.input_builder.build(collection["records"])
        if not evidence:
            return {
                "success": False,
                "status": "no_high_quality_public_signals",
                "collection_errors": collection["errors"],
                "records_collected": len(collection["records"]),
            }

        result = self.discovery.run(evidence)
        result["ranked_opportunities"] = self.linker.link(result.get("ranked_opportunities", []))
        result["public_collection"] = {
            "records_collected": len(collection["records"]),
            "evidence_used": len(evidence),
            "errors": collection["errors"],
        }
        return result
