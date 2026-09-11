from __future__ import annotations
from collections import defaultdict

class SemanticClusterer:
    """370: practical keyword-semantic clustering for opportunity signals."""

    THEMES = {
        "estimating_and_proposals": ("estimate","estimating","proposal","quote","bid"),
        "workflow_automation": ("manual","workflow","repetitive","automation","duplicate entry"),
        "integration_sync": ("integration","sync","api","connect","import","export"),
        "cost_reduction": ("expensive","cost","pricing","overpriced","subscription"),
        "reporting_analytics": ("report","reporting","dashboard","analytics","metrics"),
        "customer_support": ("support","ticket","customer service","response time"),
        "scheduling_operations": ("schedule","scheduling","dispatch","operations"),
        "compliance_admin": ("compliance","paperwork","form","audit","documentation"),
    }

    def cluster(self, records):
        groups = defaultdict(list)
        for r in records:
            text = f"{r.get('title','')} {r.get('text','')}".lower()
            hits = []
            for theme, terms in self.THEMES.items():
                if any(term in text for term in terms):
                    hits.append(theme)
            if not hits:
                hits = ["other_business_pain"]
            for theme in hits[:2]:
                groups[theme].append(r)
        return [
            {"theme": theme, "count": len(items), "records": items}
            for theme, items in groups.items()
        ]
