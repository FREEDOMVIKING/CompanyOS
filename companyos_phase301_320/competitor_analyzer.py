from __future__ import annotations

class CompetitorAnalyzer:
    """308: identify evidence that appears to mention alternatives/competitors/pricing."""

    KEYWORDS = ("competitor","alternative","pricing","price","subscription","per month","market leader","replace")

    def analyze(self, records):
        hits = []
        for r in records:
            text = f"{r.get('title','')} {r.get('text','')}".lower()
            matched = [k for k in self.KEYWORDS if k in text]
            if matched:
                hits.append({
                    "title": r.get("title"),
                    "source": r.get("source"),
                    "url": r.get("url"),
                    "signals": matched,
                })
        return hits
