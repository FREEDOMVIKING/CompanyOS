from __future__ import annotations

class ResearchPlanner:
    """312: create research queries from CEO business thesis and evidence gaps."""

    def plan(self, themes=None):
        themes = list(themes or [])
        base = [
            "painful repetitive business workflows",
            "software customers complain is expensive or difficult",
            "manual administrative work businesses pay employees to repeat",
            "underserved niche business software markets",
            "high willingness-to-pay operational problems",
        ]
        queries = base + [f"{x} customer problems competitors pricing" for x in themes[:5]]
        return {
            "queries": queries,
            "goal": "find evidence-backed problems with viable economics",
        }
