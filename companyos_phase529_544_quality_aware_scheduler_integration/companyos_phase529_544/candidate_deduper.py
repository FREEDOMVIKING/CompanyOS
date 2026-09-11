class CandidateDeduper:
    """536: keep one best candidate per theme."""

    def unique(self, candidates):
        best = {}
        for c in candidates:
            theme = c.get("theme") or c.get("name")
            cur = best.get(theme)
            if cur is None or float(c.get("quality_score",0)) > float(cur.get("quality_score",0)):
                best[theme] = c
        return list(best.values())
