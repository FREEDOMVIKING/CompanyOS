from __future__ import annotations
from collections import defaultdict

class ProblemClusterer:
    """342: cluster mined problems into repeatable themes."""

    KEYWORDS = {
        "time_waste": ("slow","manual","time-consuming","waste","hours"),
        "cost": ("expensive","pricing","cost","overpriced"),
        "complexity": ("difficult","complex","confusing","hard"),
        "errors": ("mistake","error","inaccurate","inconsistent"),
        "integration": ("integration","sync","duplicate entry","re-enter"),
    }

    def cluster(self, problems):
        groups = defaultdict(list)
        for p in problems:
            text = str(p.get("statement","")).lower()
            matched = False
            for theme, words in self.KEYWORDS.items():
                if any(w in text for w in words):
                    groups[theme].append(p)
                    matched = True
            if not matched:
                groups["other"].append(p)
        return [
            {"theme": theme, "count": len(items), "problems": items}
            for theme, items in groups.items()
        ]
