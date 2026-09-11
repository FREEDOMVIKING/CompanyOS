from __future__ import annotations
from .public_discovery_cycle import PublicDiscoveryCycle

class CEOPublicResearch:
    """367: CEO-facing public discovery command."""

    def __init__(self, project_root):
        self.cycle = PublicDiscoveryCycle(project_root)

    def run(self):
        result = self.cycle.run()
        if not result.get("success"):
            return result
        top = result.get("ranked_opportunities", [])[:5]
        return {
            **result,
            "ceo_summary": {
                "top_candidate_count": len(top),
                "top_candidates": [
                    {
                        "name": (x.get("opportunity") or {}).get("name"),
                        "score": x.get("score"),
                        "evidence_links": x.get("evidence_links", [])[:5],
                        "validation_plan": x.get("validation_plan"),
                    }
                    for x in top
                ],
                "decision_rule": "validate before major build commitment",
            },
        }
