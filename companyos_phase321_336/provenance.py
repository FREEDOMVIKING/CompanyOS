from __future__ import annotations
from datetime import datetime, timezone

class Provenance:
    """328: attach collection provenance to evidence."""

    def attach(self, record, source):
        out = dict(record)
        md = dict(out.get("metadata") or {})
        md.update({
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "source_type": source.get("type"),
            "configured_source_url": source.get("url"),
        })
        out["metadata"] = md
        return out
