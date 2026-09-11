from __future__ import annotations
import json

class JSONSource:
    """324: configurable JSON-list extraction."""

    def parse(self, body, source):
        data = json.loads(body.decode("utf-8", errors="replace"))
        path = source.get("items_path", "")
        items = data

        if path:
            for part in path.split("."):
                if isinstance(items, dict):
                    items = items.get(part)
                else:
                    items = None
                    break

        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list):
            return []

        title_key = source.get("title_key", "title")
        text_key = source.get("text_key", "text")
        url_key = source.get("url_key", "url")
        published_key = source.get("published_key", "published_at")

        records = []
        for item in items:
            if not isinstance(item, dict):
                continue
            title = item.get(title_key) or ""
            text = item.get(text_key) or item.get("description") or item.get("body") or ""
            if not title and not text:
                continue
            records.append({
                "source": source.get("name", "json_source"),
                "title": str(title or "Untitled"),
                "text": str(text),
                "url": item.get(url_key) or source.get("url"),
                "published_at": item.get(published_key),
                "metadata": {"format": "json"},
            })
        return records
