class GoNoGoEngine:
    """395: CEO validation decision from interpreted evidence."""

    def decide(self, interpretation):
        ratio = float(interpretation.get("pass_ratio", 0))
        total = int(interpretation.get("total_checks", 0))
        if total < 2:
            return {"decision":"insufficient_evidence","confidence":0.2}
        if ratio >= 0.75:
            return {"decision":"go_to_mvp","confidence":round(ratio,2)}
        if ratio >= 0.50:
            return {"decision":"run_more_validation","confidence":round(ratio,2)}
        return {"decision":"no_go_or_pivot","confidence":round(1-ratio,2)}
