from __future__ import annotations
import json
import urllib.request

class HackerNewsSource:
    """353: collect public Hacker News stories using the official Firebase API."""

    BASE = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, timeout=20):
        self.timeout = int(timeout)

    def _json(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": "CompanyOS-Research/1.0"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def collect(self, limit=30):
        ids = self._json(f"{self.BASE}/topstories.json") or []
        records = []
        for story_id in ids[:max(1, int(limit))]:
            try:
                item = self._json(f"{self.BASE}/item/{story_id}.json") or {}
            except Exception:
                continue
            title = item.get("title") or ""
            text = item.get("text") or ""
            if not title and not text:
                continue
            records.append({
                "source": "Hacker News",
                "title": title or "Untitled",
                "text": text or title,
                "url": item.get("url") or f"https://news.ycombinator.com/item?id={story_id}",
                "published_at": item.get("time"),
                "metadata": {
                    "format": "hn_api",
                    "story_id": story_id,
                    "score": item.get("score"),
                    "descendants": item.get("descendants"),
                    "by": item.get("by"),
                },
            })
        return records
