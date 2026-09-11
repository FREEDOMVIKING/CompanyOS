from __future__ import annotations
from .rss_source import RSSSource
from .json_source import JSONSource
from .text_source import TextSource

class SourceRouter:
    """326: dispatch configured source types."""

    def __init__(self):
        self.rss = RSSSource()
        self.json = JSONSource()
        self.text = TextSource()

    def parse(self, body, source):
        typ = str(source.get("type", "text")).lower()
        if typ in ("rss", "atom", "feed"):
            return self.rss.parse(body, source.get("name", "feed"), source["url"])
        if typ == "json":
            return self.json.parse(body, source)
        return self.text.parse(body, source.get("name", "text_source"), source["url"])
