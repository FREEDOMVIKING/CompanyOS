from __future__ import annotations
import json
from pathlib import Path

class SourceRegistry:
    """321: durable registry for configured live research sources."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "research_sources.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self):
        if not self.path.exists():
            return {"sources": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {"sources": []}
        except Exception:
            return {"sources": []}

    def save(self, sources):
        payload = {"sources": list(sources)}
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return payload
