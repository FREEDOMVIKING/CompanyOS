from __future__ import annotations

class OpportunitySynthesizer:
    """310: deterministic opportunity candidates from problem clusters.

    Model-assisted synthesis can be layered on top by ProviderResearchAdapter.
    """

    def synthesize(self, problems, markets, competitors, limit=10):
        opportunities = []
        for i, p in enumerate(problems[:int(limit)]):
            statement = p.get("statement", "")
            opportunities.append({
                "name": f"Opportunity {i+1}",
                "problem": statement,
                "customer": "customer segment to validate",
                "solution": "workflow/software/service solution to validate",
                "revenue_model": "subscription or transaction model to validate",
                "evidence": [x for x in [p.get("source"), p.get("url")] if x],
                "metrics": {
                    "demand": 5,
                    "speed_to_revenue": 5,
                    "margin": 6,
                    "automation": 7,
                    "competition_advantage": 4 if competitors else 5,
                    "recurring_revenue": 6,
                    "capital_efficiency": 7,
                },
                "discovery_metadata": {
                    "market_themes": markets[:5],
                    "competitor_signal_count": len(competitors),
                },
            })
        return opportunities
