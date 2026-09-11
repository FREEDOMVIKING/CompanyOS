class CustomerFeedback:
    """451: normalize customer feedback into actionable themes."""

    THEMES = {
        "usability": ("confusing","hard to use","difficult","ui","ux"),
        "missing_feature": ("missing","wish","feature request","need"),
        "reliability": ("bug","broken","error","crash","failed"),
        "pricing": ("price","pricing","expensive","cost"),
        "value": ("helpful","saved time","worth","useful","value"),
    }

    def classify(self, items):
        out = []
        for item in items:
            text = str(item.get("text","")).lower()
            hits = [theme for theme, terms in self.THEMES.items() if any(t in text for t in terms)]
            out.append({**item, "themes":hits or ["other"]})
        return out
