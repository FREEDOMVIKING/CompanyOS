from collections import defaultdict

class CrossSignalSynthesizer:
    """520: group multiple related signals into stronger candidate evidence sets."""

    THEMES = {
        "estimating_proposals":("estimate","estimating","proposal","bid","quote"),
        "workflow_automation":("manual","workflow","repetitive","automation"),
        "integration_sync":("integration","sync","api","import","export"),
        "cost_optimization":("expensive","pricing","cost","subscription"),
        "reporting_analytics":("reporting","dashboard","analytics","metrics"),
        "support_ops":("support","ticket","customer service"),
        "scheduling_dispatch":("schedule","dispatch","field service"),
    }

    def synthesize(self, records):
        groups = defaultdict(list)
        for r in records:
            text = f"{r.get('title','')} {r.get('text','')}".lower()
            matched = False
            for theme, terms in self.THEMES.items():
                if any(t in text for t in terms):
                    groups[theme].append(r)
                    matched = True
            if not matched:
                groups["other_business_pain"].append(r)
        return [
            {"theme":k,"records":v,"count":len(v),"sources":sorted({x.get("source") for x in v if x.get("source")})}
            for k,v in groups.items()
        ]
