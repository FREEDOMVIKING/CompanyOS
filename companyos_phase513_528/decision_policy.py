class DecisionPolicy:
    """523: build/validate/research/reject policy."""

    def decide(self, candidate):
        quality = float(candidate.get("quality_score",0))
        pain = float((candidate.get("dimensions") or {}).get("pain",0))
        intent = float((candidate.get("dimensions") or {}).get("commercial_intent",0))
        sources = int(candidate.get("source_count",0))

        if quality >= 7.5 and pain >= 5 and intent >= 4 and sources >= 2:
            action = "priority_validate"
        elif quality >= 6.0 and pain >= 4:
            action = "validate"
        elif quality >= 4.5:
            action = "research_more"
        else:
            action = "reject"
        return {"decision":action,"quality_score":quality}
