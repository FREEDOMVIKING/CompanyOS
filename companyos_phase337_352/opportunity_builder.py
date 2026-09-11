from __future__ import annotations

class EvidenceOpportunityBuilder:
    """345: build business candidates directly from evidence clusters."""

    def build(self, gaps, clusters):
        cluster_map = {c.get("theme"): c for c in clusters}
        out = []
        for i, gap in enumerate(gaps, 1):
            theme = gap["theme"]
            cluster = cluster_map.get(theme, {})
            evidence = []
            for p in cluster.get("problems", [])[:5]:
                evidence.extend(x for x in [p.get("source"), p.get("url")] if x)
            out.append({
                "name": f"{theme.replace('_',' ').title()} Opportunity",
                "problem": f"Repeated customer pain around {theme.replace('_',' ')}",
                "customer": "customer segment to validate from evidence",
                "solution": f"automated solution targeting {theme.replace('_',' ')}",
                "revenue_model": "subscription/service model to validate",
                "evidence": list(dict.fromkeys(evidence)),
                "metrics": {
                    "demand": min(10, 4 + gap["pain_evidence_count"]),
                    "speed_to_revenue": 6,
                    "margin": 7,
                    "automation": 8,
                    "competition_advantage": max(3, 8 - gap["competitor_signal_count"]),
                    "recurring_revenue": 7,
                    "capital_efficiency": 8,
                },
                "gap": gap,
            })
        return out
