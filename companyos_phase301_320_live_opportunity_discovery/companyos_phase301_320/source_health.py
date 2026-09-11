from __future__ import annotations

class SourceHealth:
    """316: quality/availability summary for configured research sources."""

    def summarize(self, records):
        by_source = {}
        for r in records:
            src = r.get("source") or "unknown"
            by_source[src] = by_source.get(src, 0) + 1
        return {
            "source_count": len(by_source),
            "records_by_source": by_source,
            "healthy": bool(records),
        }
