class CustomerFeedbackLoop:
    """1029-1036: normalize and prioritize customer feedback."""
    def summarize(self, feedback):
        rows=list(feedback or [])
        themes={}
        for item in rows:
            theme=item.get("theme","other")
            themes[theme]=themes.get(theme,0)+1
        top=sorted(themes.items(),key=lambda x:x[1],reverse=True)
        return {
            "count":len(rows),
            "themes":themes,
            "top_theme":top[0][0] if top else None,
            "actionable":[x for x in rows if x.get("severity") in ("high","critical") or x.get("revenue_impact")],
        }
