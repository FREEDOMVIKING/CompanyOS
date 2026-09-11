import json
from pathlib import Path
from datetime import datetime, timezone

class ResearchEscalationAudit:
    """837: append-only escalation audit."""

    def __init__(self, root):
        self.path = Path(root) / ".companyos_runtime" / "research_escalation_audit.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, payload):
        row = {"timestamp":datetime.now(timezone.utc).isoformat(), **payload}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, default=str) + "\n")
        return row
