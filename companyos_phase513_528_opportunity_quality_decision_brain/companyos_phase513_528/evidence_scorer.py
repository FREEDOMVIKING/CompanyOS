class EvidenceScorer:
    """515: score source strength, specificity, and actionable detail."""

    def score(self, record):
        score = 0
        text = str(record.get("text",""))
        if record.get("url"): score += 1.5
        if record.get("source"): score += 1.0
        if len(text) >= 100: score += 1.5
        if len(text) >= 300: score += 1.0
        if any(x in text.lower() for x in ("hours","cost","price","customers","users","revenue","manual")):
            score += 2.0
        if (record.get("metadata") or {}).get("comments"):
            score += 1.0
        return round(min(10, score), 2)
