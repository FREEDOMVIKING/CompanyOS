from __future__ import annotations
import json
from pathlib import Path

class StarterResearchNetwork:
    """337: install a configurable starter network without embedding secrets."""

    def __init__(self, project_root):
        self.path = Path(project_root) / ".companyos_runtime" / "research_sources.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def template(self):
        return {
            "sources": [
                {
                    "name": "Business News RSS",
                    "type": "rss",
                    "url": "REPLACE_WITH_PUBLIC_RSS_URL",
                    "enabled": False,
                    "priority": 0.8,
                    "category": "business_trends",
                },
                {
                    "name": "Industry Forum Feed",
                    "type": "rss",
                    "url": "REPLACE_WITH_PUBLIC_RSS_OR_ATOM_URL",
                    "enabled": False,
                    "priority": 0.9,
                    "category": "customer_pain",
                },
                {
                    "name": "Public Market JSON",
                    "type": "json",
                    "url": "REPLACE_WITH_PUBLIC_JSON_ENDPOINT",
                    "enabled": False,
                    "priority": 0.7,
                    "category": "market_data",
                    "items_path": "items",
                    "title_key": "title",
                    "text_key": "description",
                    "url_key": "url",
                },
                {
                    "name": "Public Industry Page",
                    "type": "text",
                    "url": "REPLACE_WITH_PUBLIC_PAGE_URL",
                    "enabled": False,
                    "priority": 0.6,
                    "category": "industry_context",
                },
            ]
        }

    def install_if_missing(self):
        if self.path.exists():
            return {"installed": False, "reason": "existing_registry_preserved", "path": str(self.path)}
        data = self.template()
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"installed": True, "path": str(self.path), "source_count": len(data["sources"])}
