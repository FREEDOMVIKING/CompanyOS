class CandidatePriority:
    """535: rank candidates by quality, source diversity, and decision urgency."""

    BOOST = {"priority_validate":2.0,"validate":1.0,"research_more":0.25,"reject":-10.0}

    def score(self, candidate):
        base = float(candidate.get("quality_score",0))
        base += min(2.0, int(candidate.get("source_count",0))*0.4)
        base += self.BOOST.get((candidate.get("decision") or {}).get("decision"),0)
        return round(base,3)

    def rank(self, candidates):
        return sorted(candidates, key=self.score, reverse=True)
