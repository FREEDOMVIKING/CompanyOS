from __future__ import annotations
from pathlib import Path
from .ceo_discovery_loop import CEODiscoveryLoop
from .evidence_store import EvidenceStore
from .validation_queue import ValidationQueue
from .discovery_memory import DiscoveryMemory

class DiscoveryOrchestrator:
    """319: persist evidence, discovery results, and validation queue."""

    def __init__(self, project_root):
        self.root = Path(project_root).resolve()
        self.loop = CEODiscoveryLoop()
        self.store = EvidenceStore(self.root)
        self.queue = ValidationQueue(self.root)
        self.memory = DiscoveryMemory(self.root)

    def run(self, records):
        for record in records:
            self.store.append(record)
        result = self.loop.run(records)
        queued = self.queue.save(result["ranked_opportunities"])
        result["validation_queue_count"] = len(queued)
        result["memory"] = self.memory.record(result)
        return result
