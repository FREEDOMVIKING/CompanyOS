class SupportTriage:
    """452: prioritize operational support issues."""

    def prioritize(self, issues):
        ranked = []
        for issue in issues:
            severity = int(issue.get("severity",1))
            affected = int(issue.get("affected_users",1))
            revenue_risk = float(issue.get("revenue_risk",0))
            score = severity*3 + min(10, affected)*0.5 + min(10, revenue_risk)*0.5
            ranked.append({**issue, "priority_score":round(score,2)})
        return sorted(ranked, key=lambda x:x["priority_score"], reverse=True)
