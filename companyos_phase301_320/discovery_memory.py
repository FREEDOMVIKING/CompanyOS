from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

class DiscoveryMemory:
    """314: persistent record of discovery cycles and winners."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "opportunity_discovery_memory.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, result):
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": result.get("status"),
            "evidence_count": result.get("evidence_count"),
            "problem_count": result.get("problem_count"),
            "top_opportunities": result.get("ranked_opportunities", [])[:5],
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
