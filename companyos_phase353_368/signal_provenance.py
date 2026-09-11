from __future__ import annotations
from datetime import datetime, timezone

class SignalProvenance:
    """359: attach source and collection provenance."""

    def attach(self, records, collection_name):
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                **r,
                "metadata": {
                    **(r.get("metadata") or {}),
                    "collection_name": collection_name,
                    "collected_at": now,
                },
            }
            for r in records
        ]
