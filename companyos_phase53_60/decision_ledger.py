from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List

class DecisionLedger:
    """Phase 54: structured decision records for audit and learning."""
    def __init__(self):
        self.entries: List[Dict[str, Any]] = []

    def record(self, decision: str, rationale: str, confidence: float, metadata=None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision,
            "rationale": rationale,
            "confidence": max(0.0, min(1.0, float(confidence))),
            "metadata": metadata or {},
        }
        self.entries.append(entry)
        return entry
