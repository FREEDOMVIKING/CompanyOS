from __future__ import annotations

class SignalQuality:
    """362: score public signals before opportunity synthesis."""

    def score(self, record):
        score = 0
        text = str(record.get("text",""))
        if record.get("title"): score += 2
        if len(text) >= 80: score += 2
        if record.get("url"): score += 2
        if record.get("pain_terms"): score += 2
        md = record.get("metadata") or {}
        if (md.get("comments") or md.get("descendants") or 0) > 0: score += 1
        if record.get("source") in ("Hacker News","GitHub Issues"): score += 1
        return min(10, score)
