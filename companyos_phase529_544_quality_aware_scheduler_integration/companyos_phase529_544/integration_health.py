class IntegrationHealth:
    """543: integration-level sanity checks."""

    def evaluate(self, result):
        missions = result.get("generated_missions",[])
        candidates = result.get("candidates",[])
        invalid = [
            m for m in missions
            if m.get("mission_type") not in ("validation","research")
        ]
        return {
            "healthy": not invalid,
            "candidate_count":len(candidates),
            "mission_count":len(missions),
            "invalid_missions":invalid,
        }
