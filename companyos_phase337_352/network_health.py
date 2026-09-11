from __future__ import annotations

class ResearchNetworkHealth:
    """350: summarize live-source coverage and failure risk."""

    def summarize(self, sources, collection):
        enabled = [s for s in sources if s.get("enabled", True)]
        categories = sorted(set(s.get("category","uncategorized") for s in enabled))
        errors = collection.get("errors", [])
        records = collection.get("records", [])
        return {
            "enabled_sources": len(enabled),
            "categories": categories,
            "records_collected": len(records),
            "errors": len(errors),
            "healthy": bool(records),
            "diversity_score": len(categories),
        }
