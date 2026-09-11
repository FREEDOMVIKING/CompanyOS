from __future__ import annotations

class SourceContract:
    """301: canonical contract for external research records."""

    REQUIRED = ["source", "title", "text"]

    def normalize(self, record):
        record = dict(record or {})
        missing = [k for k in self.REQUIRED if not record.get(k)]
        return {
            "valid": not missing,
            "missing": missing,
            "record": {
                "source": record.get("source"),
                "title": record.get("title"),
                "text": record.get("text"),
                "url": record.get("url"),
                "published_at": record.get("published_at"),
                "metadata": record.get("metadata", {}),
            },
        }
