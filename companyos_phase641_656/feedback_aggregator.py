from collections import Counter

class FeedbackAggregator:
    """643: aggregate recurring customer feedback themes."""

    def summarize(self, feedback):
        themes=Counter()
        for item in feedback or []:
            for theme in item.get("themes",[]):
                themes[str(theme)] += 1
        return {
            "themes":[{"theme":k,"count":v} for k,v in themes.most_common()],
            "feedback_count":len(feedback or []),
        }
