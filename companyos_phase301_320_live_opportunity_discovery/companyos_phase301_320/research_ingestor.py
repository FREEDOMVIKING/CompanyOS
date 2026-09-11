from __future__ import annotations
from .source_contract import SourceContract
from .signal_normalizer import SignalNormalizer
from .deduper import EvidenceDeduper

class ResearchIngestor:
    """315: validate, normalize, and deduplicate live research evidence."""

    def __init__(self):
        self.contract = SourceContract()
        self.normalizer = SignalNormalizer()
        self.deduper = EvidenceDeduper()

    def ingest(self, records):
        valid = []
        rejected = []
        for raw in records:
            checked = self.contract.normalize(raw)
            if not checked["valid"]:
                rejected.append({"record": raw, "missing": checked["missing"]})
                continue
            valid.append(self.normalizer.record(checked["record"]))
        return {
            "records": self.deduper.unique(valid),
            "rejected": rejected,
        }
