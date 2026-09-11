from __future__ import annotations

class ConnectorHealth:
    """333: summarize source-connector success/failure."""

    def summarize(self, collection):
        errors = collection.get("errors", [])
        records = collection.get("records", [])
        return {
            "healthy": bool(records),
            "record_count": len(records),
            "error_count": len(errors),
            "errors": errors,
        }
