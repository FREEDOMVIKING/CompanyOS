class CandidateRouter:
    """530: route quality-brain decisions to the correct next mission."""

    def route(self, candidate):
        decision = (candidate.get("decision") or {}).get("decision")
        mapping = {
            "priority_validate":"validation",
            "validate":"validation",
            "research_more":"research_more",
            "reject":"reject",
        }
        return mapping.get(decision, "research_more")
