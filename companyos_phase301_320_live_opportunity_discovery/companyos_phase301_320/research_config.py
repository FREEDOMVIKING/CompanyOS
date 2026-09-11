from __future__ import annotations
import json, os
from pathlib import Path

class ResearchConfig:
    """302: configurable live-research settings without hardcoding vendors."""

    def __init__(self, project_root=None):
        self.root = Path(project_root).resolve() if project_root else None

    def load(self):
        data = {
            "max_records_per_cycle": max(5, int(os.getenv("COMPANYOS_RESEARCH_MAX_RECORDS", "80"))),
            "min_evidence_per_opportunity": max(1, int(os.getenv("COMPANYOS_MIN_EVIDENCE_PER_OPPORTUNITY", "2"))),
            "max_opportunities_per_cycle": max(1, int(os.getenv("COMPANYOS_MAX_OPPORTUNITIES_PER_CYCLE", "10"))),
            "provider_mode": os.getenv("COMPANYOS_RESEARCH_PROVIDER_MODE", "configured_sources"),
        }
        if self.root:
            cfg = self.root / ".companyos_runtime" / "research_sources.json"
            if cfg.exists():
                try:
                    parsed = json.loads(cfg.read_text(encoding="utf-8"))
                    if isinstance(parsed, dict):
                        data["sources"] = parsed.get("sources", [])
                except Exception:
                    data["sources"] = []
        return data
