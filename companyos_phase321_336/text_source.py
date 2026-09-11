from __future__ import annotations
import re
from html import unescape

class TextSource:
    """325: simple HTML/text extraction for configured public pages."""

    def parse(self, body, source_name, source_url):
        text = body.decode("utf-8", errors="replace")
        # Remove script/style blocks and tags. This is intentionally lightweight.
        text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
        title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", text)
        title = unescape(re.sub(r"\s+", " ", title_match.group(1)).strip()) if title_match else source_name
        clean = re.sub(r"(?s)<[^>]+>", " ", text)
        clean = unescape(re.sub(r"\s+", " ", clean)).strip()
        return [{
            "source": source_name,
            "title": title[:300],
            "text": clean[:20000],
            "url": source_url,
            "published_at": None,
            "metadata": {"format": "html_text"},
        }]
