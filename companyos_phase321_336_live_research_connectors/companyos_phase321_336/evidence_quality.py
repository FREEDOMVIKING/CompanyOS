from __future__ import annotations

class EvidenceQuality:
    """331: basic quality scoring for collected evidence."""

    def score(self, record):
        score = 0
        if record.get("title"):
            score += 2
        if len(str(record.get("text", ""))) >= 120:
            score += 3
        if record.get("url"):
            score += 2
        if record.get("published_at"):
            score += 1
        if record.get("source"):
            score += 2
        return min(10, score)
