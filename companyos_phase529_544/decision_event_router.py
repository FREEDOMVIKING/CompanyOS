class DecisionEventRouter:
    """539: map candidate decisions to scheduler/system events."""

    def event_for(self, candidate):
        decision = (candidate.get("decision") or {}).get("decision")
        return {
            "priority_validate":"quality_candidate_ready_for_priority_validation",
            "validate":"quality_candidate_ready_for_validation",
            "research_more":"quality_candidate_needs_more_research",
            "reject":"quality_candidate_rejected",
        }.get(decision,"quality_candidate_unknown")
